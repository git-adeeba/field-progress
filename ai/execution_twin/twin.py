from collections import defaultdict
from typing import Any


# -------------------------------------------------------------------
# Numeric helpers
# -------------------------------------------------------------------

def safe_number(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def clamp_percentage(
    value: Any,
) -> float:
    return max(
        0.0,
        min(
            100.0,
            safe_number(value),
        ),
    )


# -------------------------------------------------------------------
# Execution-event helpers
# -------------------------------------------------------------------

def normalize_execution_type(
    value: Any,
) -> str:
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def get_verified_events(
    execution_events: list[dict],
) -> list[dict]:

    return [
        event
        for event
        in execution_events
        if (
            event.get("status")
            == "verified"
        )
    ]


def get_latest_verified_event(
    execution_events: list[dict],
) -> dict | None:

    verified_events = (
        get_verified_events(
            execution_events
        )
    )

    if not verified_events:
        return None

    return max(
        verified_events,
        key=lambda event: (
            event.get("occurred_at")
            or event.get("created_at")
            or ""
        ),
    )


# -------------------------------------------------------------------
# Actual progress
# -------------------------------------------------------------------

def calculate_actual_progress(
    activity: dict,
    execution_events: list[dict],
) -> float:

    stored_progress = (
        clamp_percentage(
            activity.get(
                "actual_progress"
            )
        )
    )

    verified_events = (
        get_verified_events(
            execution_events
        )
    )

    # A verified completion event is strong
    # evidence that the activity reached 100%.
    for event in verified_events:

        execution_type = (
            normalize_execution_type(
                event.get(
                    "execution_type"
                )
            )
        )

        if execution_type in [
            "completed",
            "complete",
            "finished",
        ]:
            return 100.0

    # Otherwise activity.actual_progress is
    # authoritative because the Physical Progress
    # Engine already calculated and persisted it.
    return stored_progress


# -------------------------------------------------------------------
# Execution state
# -------------------------------------------------------------------

def determine_execution_state(
    activity: dict,
    execution_events: list[dict],
    actual_progress: float,
) -> str:

    if actual_progress >= 100:
        return "completed"

    latest_event = (
        get_latest_verified_event(
            execution_events
        )
    )

    activity_status = (
        str(
            activity.get("status")
            or ""
        )
        .strip()
        .lower()
    )

    if activity_status in [
        "delayed",
        "blocked",
    ]:
        return "blocked"

    if actual_progress > 0:
        return "in_progress"

    if latest_event:

        execution_type = (
            normalize_execution_type(
                latest_event.get(
                    "execution_type"
                )
            )
        )

        if execution_type in [
            "blocked",
            "delayed",
        ]:
            return "blocked"

        if execution_type in [
            "started",
            "in_progress",
            "ongoing",
        ]:
            return "in_progress"

    return "not_started"


# -------------------------------------------------------------------
# Plan-vs-actual state
# -------------------------------------------------------------------

def determine_plan_state(
    planned_progress: float,
    actual_progress: float,
    tolerance: float = 5.0,
) -> str:

    variance = (
        actual_progress
        - planned_progress
    )

    if variance > tolerance:
        return "ahead"

    if variance < -tolerance:
        return "behind"

    return "on_track"


# -------------------------------------------------------------------
# Quantity state
# -------------------------------------------------------------------

def build_quantity_progress(
    activity: dict,
) -> dict | None:

    planned_quantity = (
        activity.get(
            "planned_quantity"
        )
    )

    if planned_quantity is None:
        return None

    planned_quantity = (
        safe_number(
            planned_quantity
        )
    )

    if planned_quantity <= 0:
        return None

    actual_quantity = (
        safe_number(
            activity.get(
                "actual_quantity"
            )
        )
    )

    completion = (
        actual_quantity
        / planned_quantity
        * 100.0
    )

    return {
        "planned_quantity":
            planned_quantity,

        "actual_quantity":
            actual_quantity,

        "remaining_quantity":
            max(
                0.0,
                planned_quantity
                - actual_quantity,
            ),

        "completion_percent":
            clamp_percentage(
                completion
            ),

        "unit":
            activity.get(
                "quantity_unit"
            ),
    }


# -------------------------------------------------------------------
# Progress source
# -------------------------------------------------------------------

def determine_progress_source(
    activity: dict,
    execution_events: list[dict],
) -> str:

    latest_event = (
        get_latest_verified_event(
            execution_events
        )
    )

    if latest_event is None:

        if safe_number(
            activity.get(
                "actual_progress"
            )
        ) > 0:
            return (
                "stored_activity_progress"
            )

        return "none"

    # ---------------------------------------------------------------
    # V2:
    # Exact method persisted by Physical Progress Engine
    # ---------------------------------------------------------------

    stored_method = (
        latest_event.get(
            "progress_method"
        )
    )

    if stored_method:
        return str(
            stored_method
        )

    # ---------------------------------------------------------------
    # Backward-compatible inference for historical events
    # created before progress_method existed.
    #
    # IMPORTANT:
    # We intentionally do NOT pretend to know whether
    # historical quantity events were incremental or cumulative.
    # ---------------------------------------------------------------

    quantity = (
        latest_event.get(
            "quantity"
        )
    )

    planned_quantity = (
        activity.get(
            "planned_quantity"
        )
    )

    if (
        quantity is not None
        and planned_quantity is not None
    ):
        return "quantity_based"

    execution_type = (
        normalize_execution_type(
            latest_event.get(
                "execution_type"
            )
        )
    )

    if execution_type in [
        "completed",
        "complete",
        "finished",
    ]:
        return "completion_state"

    contribution = (
        safe_number(
            latest_event.get(
                "progress_contribution"
            )
        )
    )

    if contribution != 0:
        return (
            "verified_progress_update"
        )

    return "status_only"


# -------------------------------------------------------------------
# Evidence provenance
# -------------------------------------------------------------------

def build_latest_evidence(
    execution_events: list[dict],
    field_events_by_id: dict[str, dict],
) -> dict | None:

    latest_event = (
        get_latest_verified_event(
            execution_events
        )
    )

    if latest_event is None:
        return None

    field_event_id = (
        latest_event.get(
            "field_event_id"
        )
    )

    field_event = None

    if field_event_id:
        field_event = (
            field_events_by_id.get(
                str(field_event_id)
            )
        )

    evidence = {
        "execution_event_id":
            latest_event.get("id"),

        "field_event_id":
            field_event_id,

        "execution_type":
            normalize_execution_type(
                latest_event.get(
                    "execution_type"
                )
            ),

        "progress_method":
            latest_event.get(
                "progress_method"
            ),

        "quantity":
            latest_event.get(
                "quantity"
            ),

        "unit":
            latest_event.get(
                "unit"
            ),

        "progress_contribution":
            safe_number(
                latest_event.get(
                    "progress_contribution"
                )
            ),

        "occurred_at":
            latest_event.get(
                "occurred_at"
            ),

        "verification_status":
            latest_event.get(
                "status"
            ),
    }

    if field_event:

        evidence.update(
            {
                "source_type":
                    field_event.get(
                        "source_type"
                    ),

                "raw_text":
                    field_event.get(
                        "raw_text"
                    ),

                "reported_by":
                    field_event.get(
                        "reported_by"
                    ),

                "field_event_status":
                    field_event.get(
                        "status"
                    ),

                "field_event_created_at":
                    field_event.get(
                        "created_at"
                    ),

                "field_event_updated_at":
                    field_event.get(
                        "updated_at"
                    ),
            }
        )

    else:

        evidence.update(
            {
                "source_type":
                    None,

                "raw_text":
                    None,

                "reported_by":
                    None,

                "field_event_status":
                    None,

                "field_event_created_at":
                    None,

                "field_event_updated_at":
                    None,
            }
        )

    return evidence


# -------------------------------------------------------------------
# Build one activity in the Field Twin
# -------------------------------------------------------------------

def build_twin_activity(
    activity: dict,
    execution_events: list[dict],
    field_events_by_id: dict[str, dict],
) -> dict:

    planned_progress = (
        clamp_percentage(
            activity.get(
                "planned_progress"
            )
        )
    )

    actual_progress = (
        calculate_actual_progress(
            activity,
            execution_events,
        )
    )

    variance = (
        actual_progress
        - planned_progress
    )

    execution_state = (
        determine_execution_state(
            activity=activity,
            execution_events=(
                execution_events
            ),
            actual_progress=(
                actual_progress
            ),
        )
    )

    plan_state = (
        determine_plan_state(
            planned_progress=(
                planned_progress
            ),
            actual_progress=(
                actual_progress
            ),
        )
    )

    quantity_progress = (
        build_quantity_progress(
            activity
        )
    )

    progress_source = (
        determine_progress_source(
            activity=activity,
            execution_events=(
                execution_events
            ),
        )
    )

    latest_evidence = (
        build_latest_evidence(
            execution_events=(
                execution_events
            ),
            field_events_by_id=(
                field_events_by_id
            ),
        )
    )

    verified_events = (
        get_verified_events(
            execution_events
        )
    )

    return {
        "activity_id":
            activity.get("id"),

        "activity_code":
            activity.get(
                "activity_code"
            ),

        "activity_name":
            activity.get(
                "activity_name"
            ),

        "wbs_level":
            activity.get(
                "wbs_level"
            ),

        "discipline":
            activity.get(
                "discipline"
            ),

        "area":
            activity.get("area"),

        "planned_start":
            activity.get(
                "planned_start"
            ),

        "planned_finish":
            activity.get(
                "planned_finish"
            ),

        "actual_start":
            activity.get(
                "actual_start"
            ),

        "actual_finish":
            activity.get(
                "actual_finish"
            ),

        "planned_progress":
            planned_progress,

        "actual_progress":
            actual_progress,

        # Preferred V2 name.
        "variance":
            variance,

        # Backward-compatible V1 name.
        "progress_difference":
            variance,

        "execution_state":
            execution_state,

        # Preferred V2 name.
        "schedule_state":
            plan_state,

        # Backward-compatible V1 name.
        "plan_state":
            plan_state,

        "progress_source":
            progress_source,

        "planned_quantity":
            (
                safe_number(
                    activity.get(
                        "planned_quantity"
                    )
                )
                if activity.get(
                    "planned_quantity"
                )
                is not None
                else None
            ),

        "actual_quantity":
            (
                safe_number(
                    activity.get(
                        "actual_quantity"
                    )
                )
                if activity.get(
                    "actual_quantity"
                )
                is not None
                else None
            ),

        "quantity_unit":
            activity.get(
                "quantity_unit"
            ),

        "quantity_progress":
            quantity_progress,

        "evidence_count":
            len(
                verified_events
            ),

        "latest_evidence":
            latest_evidence,

        # Useful raw schedule status for debugging/UI.
        "activity_status":
            activity.get(
                "status"
            ),
    }


# -------------------------------------------------------------------
# Build project Field Execution Twin
# -------------------------------------------------------------------

def build_project_twin(
    project: dict,
    activities: list[dict],
    execution_events: list[dict],
    field_events: list[dict],
) -> dict:

    execution_by_activity = (
        defaultdict(list)
    )

    for event in execution_events:

        activity_id = (
            event.get(
                "activity_id"
            )
        )

        if activity_id:
            execution_by_activity[
                str(activity_id)
            ].append(
                event
            )

    field_events_by_id = {
        str(event["id"]):
            event
        for event
        in field_events
        if event.get("id")
    }

    twin_activities = []

    for activity in activities:

        activity_id = str(
            activity.get("id")
        )

        activity_execution_events = (
            execution_by_activity.get(
                activity_id,
                [],
            )
        )

        twin_activity = (
            build_twin_activity(
                activity=activity,
                execution_events=(
                    activity_execution_events
                ),
                field_events_by_id=(
                    field_events_by_id
                ),
            )
        )

        twin_activities.append(
            twin_activity
        )

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------

    total_activities = len(
        twin_activities
    )

    completed = sum(
        1
        for item
        in twin_activities
        if item[
            "execution_state"
        ]
        == "completed"
    )

    in_progress = sum(
        1
        for item
        in twin_activities
        if item[
            "execution_state"
        ]
        == "in_progress"
    )

    blocked = sum(
        1
        for item
        in twin_activities
        if item[
            "execution_state"
        ]
        == "blocked"
    )

    not_started = sum(
        1
        for item
        in twin_activities
        if item[
            "execution_state"
        ]
        == "not_started"
    )

    ahead = sum(
        1
        for item
        in twin_activities
        if item[
            "plan_state"
        ]
        == "ahead"
    )

    behind = sum(
        1
        for item
        in twin_activities
        if item[
            "plan_state"
        ]
        == "behind"
    )

    on_track = sum(
        1
        for item
        in twin_activities
        if item[
            "plan_state"
        ]
        == "on_track"
    )

    with_evidence = sum(
        1
        for item
        in twin_activities
        if item[
            "evidence_count"
        ] > 0
    )

    no_field_evidence = (
        total_activities
        - with_evidence
    )

    quantity_tracked = sum(
        1
        for item
        in twin_activities
        if item[
            "quantity_progress"
        ]
        is not None
    )

    average_planned = (
        sum(
            item[
                "planned_progress"
            ]
            for item
            in twin_activities
        )
        / total_activities
        if total_activities
        else 0.0
    )

    average_actual = (
        sum(
            item[
                "actual_progress"
            ]
            for item
            in twin_activities
        )
        / total_activities
        if total_activities
        else 0.0
    )

    average_variance = (
        sum(
            item[
                "variance"
            ]
            for item
            in twin_activities
        )
        / total_activities
        if total_activities
        else 0.0
    )

    return {
        "project": {
            "id":
                project.get("id"),

            "name":
                project.get("name"),

            "status":
                project.get(
                    "status"
                ),
        },

        "summary": {
            "total_activities":
                total_activities,

            "completed":
                completed,

            "in_progress":
                in_progress,

            "blocked":
                blocked,

            "not_started":
                not_started,

            "ahead":
                ahead,

            "behind":
                behind,

            "on_track":
                on_track,

            "with_field_evidence":
                with_evidence,

            "no_field_evidence":
                no_field_evidence,

            "quantity_tracked_activities":
                quantity_tracked,

            "average_planned_progress":
                round(
                    average_planned,
                    2,
                ),

            "average_actual_progress":
                round(
                    average_actual,
                    2,
                ),

            "average_variance":
                round(
                    average_variance,
                    2,
                ),
        },

        "activities":
            twin_activities,
    }