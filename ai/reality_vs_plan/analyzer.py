from datetime import (
    datetime,
    timezone,
)
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

PLAN_VARIANCE_TOLERANCE = 5.0

HIGH_VARIANCE_THRESHOLD = 25.0

CRITICAL_VARIANCE_THRESHOLD = 40.0

MISSING_UPDATE_MIN_PLANNED_PROGRESS = 10.0


# ============================================================
# HELPERS
# ============================================================

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


def utc_now_iso() -> str:

    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


def normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def determine_variance_severity(
    variance: float,
) -> str:

    absolute_variance = abs(
        variance
    )

    if (
        absolute_variance
        >= CRITICAL_VARIANCE_THRESHOLD
    ):
        return "critical"

    if (
        absolute_variance
        >= HIGH_VARIANCE_THRESHOLD
    ):
        return "high"

    if (
        absolute_variance
        > PLAN_VARIANCE_TOLERANCE
    ):
        return "medium"

    return "low"


def build_fingerprint(
    project_id: str,
    exception_type: str,
    activity_id: str | None = None,
    field_event_id: str | None = None,
) -> str:

    identity = (
        activity_id
        or field_event_id
        or "project"
    )

    return (
        f"{project_id}:"
        f"{exception_type}:"
        f"{identity}"
    )


# ============================================================
# EXCEPTION BUILDERS
# ============================================================

def build_ahead_of_plan_exception(
    project_id: str,
    activity: dict,
) -> dict:

    activity_id = str(
        activity.get(
            "activity_id"
        )
    )

    activity_code = (
        activity.get(
            "activity_code"
        )
        or activity_id
    )

    activity_name = (
        activity.get(
            "activity_name"
        )
        or "Unnamed activity"
    )

    planned_progress = safe_number(
        activity.get(
            "planned_progress"
        )
    )

    actual_progress = safe_number(
        activity.get(
            "actual_progress"
        )
    )

    variance = (
        actual_progress
        - planned_progress
    )

    severity = (
        determine_variance_severity(
            variance
        )
    )

    return {
        "project_id":
            project_id,

        "activity_id":
            activity_id,

        "source_field_event_id":
            None,

        "exception_type":
            "AHEAD_OF_PLAN",

        "severity":
            severity,

        "title":
            (
                f"{activity_code} is "
                "ahead of plan"
            ),

        "description":
            (
                f"{activity_name} has "
                f"{actual_progress:.2f}% actual "
                f"progress against "
                f"{planned_progress:.2f}% planned "
                f"progress, producing a "
                f"+{variance:.2f}% variance."
            ),

        "planned_progress":
            round(
                planned_progress,
                2,
            ),

        "actual_progress":
            round(
                actual_progress,
                2,
            ),

        "variance":
            round(
                variance,
                2,
            ),

        "fingerprint":
            build_fingerprint(
                project_id=project_id,
                exception_type=(
                    "AHEAD_OF_PLAN"
                ),
                activity_id=activity_id,
            ),

        "status":
            "open",
    }


def build_behind_plan_exception(
    project_id: str,
    activity: dict,
) -> dict:

    activity_id = str(
        activity.get(
            "activity_id"
        )
    )

    activity_code = (
        activity.get(
            "activity_code"
        )
        or activity_id
    )

    activity_name = (
        activity.get(
            "activity_name"
        )
        or "Unnamed activity"
    )

    planned_progress = safe_number(
        activity.get(
            "planned_progress"
        )
    )

    actual_progress = safe_number(
        activity.get(
            "actual_progress"
        )
    )

    variance = (
        actual_progress
        - planned_progress
    )

    severity = (
        determine_variance_severity(
            variance
        )
    )

    return {
        "project_id":
            project_id,

        "activity_id":
            activity_id,

        "source_field_event_id":
            None,

        "exception_type":
            "BEHIND_PLAN",

        "severity":
            severity,

        "title":
            (
                f"{activity_code} is "
                "behind plan"
            ),

        "description":
            (
                f"{activity_name} has "
                f"{actual_progress:.2f}% actual "
                f"progress against "
                f"{planned_progress:.2f}% planned "
                f"progress, producing a "
                f"{variance:.2f}% variance."
            ),

        "planned_progress":
            round(
                planned_progress,
                2,
            ),

        "actual_progress":
            round(
                actual_progress,
                2,
            ),

        "variance":
            round(
                variance,
                2,
            ),

        "fingerprint":
            build_fingerprint(
                project_id=project_id,
                exception_type=(
                    "BEHIND_PLAN"
                ),
                activity_id=activity_id,
            ),

        "status":
            "open",
    }


def build_blocked_exception(
    project_id: str,
    activity: dict,
) -> dict:

    activity_id = str(
        activity.get(
            "activity_id"
        )
    )

    activity_code = (
        activity.get(
            "activity_code"
        )
        or activity_id
    )

    activity_name = (
        activity.get(
            "activity_name"
        )
        or "Unnamed activity"
    )

    planned_progress = safe_number(
        activity.get(
            "planned_progress"
        )
    )

    actual_progress = safe_number(
        activity.get(
            "actual_progress"
        )
    )

    variance = (
        actual_progress
        - planned_progress
    )

    return {
        "project_id":
            project_id,

        "activity_id":
            activity_id,

        "source_field_event_id":
            (
                (
                    activity.get(
                        "latest_evidence"
                    )
                    or {}
                )
                .get(
                    "field_event_id"
                )
            ),

        "exception_type":
            "BLOCKED_ACTIVITY",

        "severity":
            "high",

        "title":
            (
                f"{activity_code} is blocked"
            ),

        "description":
            (
                f"{activity_name} is currently "
                "reported as blocked or delayed "
                "in the Field Execution Twin."
            ),

        "planned_progress":
            round(
                planned_progress,
                2,
            ),

        "actual_progress":
            round(
                actual_progress,
                2,
            ),

        "variance":
            round(
                variance,
                2,
            ),

        "fingerprint":
            build_fingerprint(
                project_id=project_id,
                exception_type=(
                    "BLOCKED_ACTIVITY"
                ),
                activity_id=activity_id,
            ),

        "status":
            "open",
    }


def build_missing_update_exception(
    project_id: str,
    activity: dict,
) -> dict:

    activity_id = str(
        activity.get(
            "activity_id"
        )
    )

    activity_code = (
        activity.get(
            "activity_code"
        )
        or activity_id
    )

    activity_name = (
        activity.get(
            "activity_name"
        )
        or "Unnamed activity"
    )

    planned_progress = safe_number(
        activity.get(
            "planned_progress"
        )
    )

    actual_progress = safe_number(
        activity.get(
            "actual_progress"
        )
    )

    variance = (
        actual_progress
        - planned_progress
    )

    return {
        "project_id":
            project_id,

        "activity_id":
            activity_id,

        "source_field_event_id":
            None,

        "exception_type":
            "MISSING_UPDATE",

        "severity":
            (
                "high"
                if planned_progress >= 50
                else "medium"
            ),

        "title":
            (
                f"No field evidence for "
                f"{activity_code}"
            ),

        "description":
            (
                f"{activity_name} has "
                f"{planned_progress:.2f}% planned "
                "progress but no verified field "
                "evidence has been linked to it."
            ),

        "planned_progress":
            round(
                planned_progress,
                2,
            ),

        "actual_progress":
            round(
                actual_progress,
                2,
            ),

        "variance":
            round(
                variance,
                2,
            ),

        "fingerprint":
            build_fingerprint(
                project_id=project_id,
                exception_type=(
                    "MISSING_UPDATE"
                ),
                activity_id=activity_id,
            ),

        "status":
            "open",
    }


def build_unplanned_work_exception(
    project_id: str,
    field_event: dict,
) -> dict:

    field_event_id = str(
        field_event.get(
            "id"
        )
    )

    raw_text = (
        field_event.get(
            "raw_text"
        )
        or "Unplanned field work"
    )

    return {
        "project_id":
            project_id,

        "activity_id":
            None,

        "source_field_event_id":
            field_event_id,

        "exception_type":
            "UNPLANNED_WORK",

        "severity":
            "high",

        "title":
            "Unplanned field work detected",

        "description":
            (
                "A field update exists without "
                "a verified schedule activity "
                f"link: {raw_text}"
            ),

        "planned_progress":
            None,

        "actual_progress":
            None,

        "variance":
            None,

        "fingerprint":
            build_fingerprint(
                project_id=project_id,
                exception_type=(
                    "UNPLANNED_WORK"
                ),
                field_event_id=(
                    field_event_id
                ),
            ),

        "status":
            "open",
    }


# ============================================================
# ACTIVITY ANALYSIS
# ============================================================

def analyze_twin_activity(
    project_id: str,
    activity: dict,
) -> list[dict]:

    exceptions = []

    planned_progress = safe_number(
        activity.get(
            "planned_progress"
        )
    )

    actual_progress = safe_number(
        activity.get(
            "actual_progress"
        )
    )

    variance = (
        actual_progress
        - planned_progress
    )

    execution_state = normalize_text(
        activity.get(
            "execution_state"
        )
    )

    evidence_count = int(
        safe_number(
            activity.get(
                "evidence_count"
            )
        )
    )

    # --------------------------------------------------------
    # BLOCKED
    # --------------------------------------------------------

    if execution_state == "blocked":

        exceptions.append(
            build_blocked_exception(
                project_id=project_id,
                activity=activity,
            )
        )

    # --------------------------------------------------------
    # AHEAD OF PLAN
    # --------------------------------------------------------

    if (
        variance
        > PLAN_VARIANCE_TOLERANCE
    ):

        exceptions.append(
            build_ahead_of_plan_exception(
                project_id=project_id,
                activity=activity,
            )
        )

    # --------------------------------------------------------
    # BEHIND PLAN
    # --------------------------------------------------------

    elif (
        variance
        < -PLAN_VARIANCE_TOLERANCE
    ):

        exceptions.append(
            build_behind_plan_exception(
                project_id=project_id,
                activity=activity,
            )
        )

    # --------------------------------------------------------
    # MISSING FIELD UPDATE
    #
    # Avoid generating noise for activities with tiny
    # planned progress or future/not-yet-active activities.
    # --------------------------------------------------------

    if (
        planned_progress
        >= MISSING_UPDATE_MIN_PLANNED_PROGRESS
        and evidence_count == 0
        and actual_progress <= 0
    ):

        exceptions.append(
            build_missing_update_exception(
                project_id=project_id,
                activity=activity,
            )
        )

    return exceptions


# ============================================================
# UNPLANNED FIELD WORK
# ============================================================

def detect_unplanned_work(
    project_id: str,
    field_events: list[dict],
    activity_matches: list[dict],
) -> list[dict]:

    approved_field_event_ids = set()

    suggested_field_event_ids = set()

    for match in activity_matches:

        field_event_id = (
            match.get(
                "field_event_id"
            )
        )

        if not field_event_id:
            continue

        status = normalize_text(
            match.get(
                "status"
            )
        )

        if status == "approved":

            approved_field_event_ids.add(
                str(field_event_id)
            )

        elif status == "suggested":

            suggested_field_event_ids.add(
                str(field_event_id)
            )

    exceptions = []

    for event in field_events:

        field_event_id = (
            event.get(
                "id"
            )
        )

        if not field_event_id:
            continue

        field_event_id = str(
            field_event_id
        )

        event_status = normalize_text(
            event.get(
                "status"
            )
        )

        # If planner has already approved a schedule
        # activity relationship, it is not unplanned.
        if (
            field_event_id
            in approved_field_event_ids
        ):
            continue

        # Suggested matches are ambiguity/review cases,
        # not yet confirmed unplanned work.
        if (
            field_event_id
            in suggested_field_event_ids
        ):
            continue

        # Pending raw field evidence should first go through
        # matching; don't prematurely call it unplanned.
        if event_status in [
            "pending",
            "",
        ]:
            continue

        # Explicitly flagged/unmatched field evidence is
        # meaningful evidence of work outside the schedule.
        if event_status in [
            "flagged",
            "unplanned",
            "unmatched",
            "no_match",
        ]:

            exceptions.append(
                build_unplanned_work_exception(
                    project_id=project_id,
                    field_event=event,
                )
            )

    return exceptions


# ============================================================
# PROJECT ANALYSIS
# ============================================================

def analyze_project_reality_vs_plan(
    twin: dict,
    field_events: list[dict],
    activity_matches: list[dict],
) -> dict:

    project = (
        twin.get(
            "project"
        )
        or {}
    )

    project_id = str(
        project.get(
            "id"
        )
        or ""
    )

    if not project_id:

        raise ValueError(
            "Field Twin does not contain project id."
        )

    activities = (
        twin.get(
            "activities"
        )
        or []
    )

    findings = []

    for activity in activities:

        findings.extend(
            analyze_twin_activity(
                project_id=project_id,
                activity=activity,
            )
        )

    findings.extend(
        detect_unplanned_work(
            project_id=project_id,
            field_events=field_events,
            activity_matches=(
                activity_matches
            ),
        )
    )

    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    type_counts = {}

    for finding in findings:

        severity = (
            finding.get(
                "severity"
            )
            or "medium"
        )

        if severity not in severity_counts:
            severity_counts[
                severity
            ] = 0

        severity_counts[
            severity
        ] += 1

        exception_type = (
            finding.get(
                "exception_type"
            )
            or "UNKNOWN"
        )

        type_counts[
            exception_type
        ] = (
            type_counts.get(
                exception_type,
                0,
            )
            + 1
        )

    findings.sort(
        key=lambda item: (
            {
                "critical": 4,
                "high": 3,
                "medium": 2,
                "low": 1,
            }.get(
                item.get(
                    "severity"
                ),
                0,
            ),
            abs(
                safe_number(
                    item.get(
                        "variance"
                    )
                )
            ),
        ),
        reverse=True,
    )

    return {
        "project": project,

        "generated_at":
            utc_now_iso(),

        "summary": {
            "total_exceptions":
                len(findings),

            "severity_counts":
                severity_counts,

            "type_counts":
                type_counts,
        },

        "exceptions":
            findings,
    }