from datetime import (
    datetime,
    timezone,
)

import math

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from pydantic import BaseModel

from app.database.auth_dependency import (
    get_current_user,
)

from app.database.supabase import (
    supabase,
)

from ai.execution_twin.twin import (
    build_project_twin,
)

from ai.reality_vs_plan.analyzer import (
    analyze_project_reality_vs_plan,
)


router = APIRouter(
    prefix="/exceptions",
    tags=[
        "Reality vs Plan / Exceptions"
    ],
)


# ============================================================
# CONFIGURATION
# ============================================================

EXCEPTION_BATCH_SIZE = 100

DATABASE_PAGE_SIZE = 1000

DEFAULT_PAGE_SIZE = 25

MAX_PAGE_SIZE = 100


SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


# ============================================================
# REQUEST MODELS
# ============================================================

class ResolveExceptionRequest(
    BaseModel
):
    resolution_note: str | None = None


# ============================================================
# BASIC HELPERS
# ============================================================

def utc_now_iso() -> str:

    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


def normalize_text(
    value,
) -> str:

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


def safe_number(
    value,
) -> float:

    try:

        if value is None:
            return 0.0

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


def chunk_list(
    items: list,
    size: int,
):

    for start in range(
        0,
        len(items),
        size,
    ):

        yield items[
            start:
            start + size
        ]


# ============================================================
# GET PROJECT
# ============================================================

def get_project(
    project_id: str,
) -> dict:

    response = (
        supabase
        .table("projects")
        .select("*")
        .eq(
            "id",
            project_id,
        )
        .limit(1)
        .execute()
    )

    if not response.data:

        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return response.data[0]


# ============================================================
# PAGINATED ACTIVITY FETCH
# ============================================================

def get_all_project_activities(
    project_id: str,
) -> list[dict]:

    all_activities = []

    start = 0

    while True:

        end = (
            start
            + DATABASE_PAGE_SIZE
            - 1
        )

        response = (
            supabase
            .table("activities")
            .select("*")
            .eq(
                "project_id",
                project_id,
            )
            .order(
                "id",
            )
            .range(
                start,
                end,
            )
            .execute()
        )

        rows = (
            response.data
            or []
        )

        all_activities.extend(
            rows
        )

        if (
            len(rows)
            < DATABASE_PAGE_SIZE
        ):
            break

        start += (
            DATABASE_PAGE_SIZE
        )

    return all_activities


# ============================================================
# PAGINATED EXECUTION EVENT FETCH
# ============================================================

def get_project_execution_events(
    project_id: str,
) -> list[dict]:

    all_events = []

    start = 0

    while True:

        end = (
            start
            + DATABASE_PAGE_SIZE
            - 1
        )

        response = (
            supabase
            .table(
                "execution_events"
            )
            .select("*")
            .eq(
                "project_id",
                project_id,
            )
            .order(
                "occurred_at",
                desc=True,
            )
            .order(
                "id",
                desc=True,
            )
            .range(
                start,
                end,
            )
            .execute()
        )

        rows = (
            response.data
            or []
        )

        all_events.extend(
            rows
        )

        if (
            len(rows)
            < DATABASE_PAGE_SIZE
        ):
            break

        start += (
            DATABASE_PAGE_SIZE
        )

    return all_events


# ============================================================
# PAGINATED FIELD EVENT FETCH
# ============================================================

def get_project_field_events(
    project_id: str,
) -> list[dict]:

    all_events = []

    start = 0

    while True:

        end = (
            start
            + DATABASE_PAGE_SIZE
            - 1
        )

        response = (
            supabase
            .table(
                "field_events"
            )
            .select("*")
            .eq(
                "project_id",
                project_id,
            )
            .order(
                "created_at",
                desc=True,
            )
            .order(
                "id",
                desc=True,
            )
            .range(
                start,
                end,
            )
            .execute()
        )

        rows = (
            response.data
            or []
        )

        all_events.extend(
            rows
        )

        if (
            len(rows)
            < DATABASE_PAGE_SIZE
        ):
            break

        start += (
            DATABASE_PAGE_SIZE
        )

    return all_events


# ============================================================
# ACTIVITY MATCH FETCH
# ============================================================

def get_project_activity_matches(
    project_id: str,
) -> list[dict]:

    field_events = (
        get_project_field_events(
            project_id
        )
    )

    field_event_ids = [
        str(row["id"])
        for row
        in field_events
        if row.get("id")
    ]

    if not field_event_ids:

        return []

    all_matches = []

    batch_size = 200

    for batch in chunk_list(
        field_event_ids,
        batch_size,
    ):

        response = (
            supabase
            .table(
                "activity_matches"
            )
            .select("*")
            .in_(
                "field_event_id",
                batch,
            )
            .execute()
        )

        all_matches.extend(
            response.data
            or []
        )

    return all_matches


# ============================================================
# PAGINATED EXCEPTION FETCH
# ============================================================

def get_all_project_exceptions(
    project_id: str,
) -> list[dict]:

    all_exceptions = []

    start = 0

    while True:

        end = (
            start
            + DATABASE_PAGE_SIZE
            - 1
        )

        response = (
            supabase
            .table("exceptions")
            .select("*")
            .eq(
                "project_id",
                project_id,
            )
            .order(
                "detected_at",
                desc=True,
            )
            .order(
                "id",
                desc=True,
            )
            .range(
                start,
                end,
            )
            .execute()
        )

        rows = (
            response.data
            or []
        )

        all_exceptions.extend(
            rows
        )

        print(
            "[EXCEPTION FETCH] "
            f"start={start}, "
            f"end={end}, "
            f"received={len(rows)}"
        )

        if (
            len(rows)
            < DATABASE_PAGE_SIZE
        ):
            break

        start += (
            DATABASE_PAGE_SIZE
        )

    print(
        "[EXCEPTION FETCH] "
        f"Total loaded: "
        f"{len(all_exceptions)}"
    )

    return all_exceptions


# ============================================================
# BUILD CURRENT PROJECT TWIN
# ============================================================

def build_current_project_twin(
    project_id: str,
) -> tuple[
    dict,
    list[dict],
    list[dict],
]:

    project = (
        get_project(
            project_id
        )
    )

    activities = (
        get_all_project_activities(
            project_id
        )
    )

    execution_events = (
        get_project_execution_events(
            project_id
        )
    )

    field_events = (
        get_project_field_events(
            project_id
        )
    )

    activity_matches = (
        get_project_activity_matches(
            project_id
        )
    )

    twin = (
        build_project_twin(
            project=project,
            activities=activities,
            execution_events=(
                execution_events
            ),
            field_events=field_events,
        )
    )

    return (
        twin,
        field_events,
        activity_matches,
    )


# ============================================================
# EXCEPTION PAYLOAD BUILDER
# ============================================================

def build_exception_payload(
    finding: dict,
    now: str,
) -> dict:

    return {
        "project_id":
            finding.get(
                "project_id"
            ),

        "activity_id":
            finding.get(
                "activity_id"
            ),

        "source_field_event_id":
            finding.get(
                "source_field_event_id"
            ),

        "exception_type":
            finding.get(
                "exception_type"
            ),

        "severity":
            finding.get(
                "severity"
            ),

        "title":
            finding.get(
                "title"
            ),

        "description":
            finding.get(
                "description"
            ),

        "planned_progress":
            finding.get(
                "planned_progress"
            ),

        "actual_progress":
            finding.get(
                "actual_progress"
            ),

        "variance":
            finding.get(
                "variance"
            ),

        "fingerprint":
            finding.get(
                "fingerprint"
            ),

        "status":
            "open",

        "updated_at":
            now,

        "resolved_at":
            None,

        "resolution_note":
            None,
    }


# ============================================================
# PERSIST GENERATED EXCEPTIONS
# ============================================================

def persist_exception_findings(
    project_id: str,
    findings: list[dict],
) -> dict:

    now = utc_now_iso()

    # --------------------------------------------------------
    # Fetch existing project exceptions once.
    # Pagination prevents the 1000-row Supabase cap.
    # --------------------------------------------------------

    existing_rows = (
        get_all_project_exceptions(
            project_id
        )
    )

    existing_by_fingerprint = {
        str(row["fingerprint"]):
            row
        for row
        in existing_rows
        if row.get(
            "fingerprint"
        )
    }

    active_fingerprints = set()

    new_payloads = []

    changed_existing = []

    unchanged_existing_count = 0

    # --------------------------------------------------------
    # Compare generated findings with existing DB rows.
    # --------------------------------------------------------

    for finding in findings:

        fingerprint = (
            finding.get(
                "fingerprint"
            )
        )

        if not fingerprint:
            continue

        fingerprint = str(
            fingerprint
        )

        active_fingerprints.add(
            fingerprint
        )

        payload = (
            build_exception_payload(
                finding=finding,
                now=now,
            )
        )

        existing = (
            existing_by_fingerprint
            .get(
                fingerprint
            )
        )

        # ----------------------------------------------------
        # New exception
        # ----------------------------------------------------

        if existing is None:

            payload[
                "detected_at"
            ] = now

            new_payloads.append(
                payload
            )

            continue

        # ----------------------------------------------------
        # Existing exception
        # ----------------------------------------------------

        meaningful_changed = any(
            [
                existing.get(
                    "exception_type"
                )
                != payload.get(
                    "exception_type"
                ),

                existing.get(
                    "severity"
                )
                != payload.get(
                    "severity"
                ),

                existing.get(
                    "title"
                )
                != payload.get(
                    "title"
                ),

                existing.get(
                    "description"
                )
                != payload.get(
                    "description"
                ),

                existing.get(
                    "planned_progress"
                )
                != payload.get(
                    "planned_progress"
                ),

                existing.get(
                    "actual_progress"
                )
                != payload.get(
                    "actual_progress"
                ),

                existing.get(
                    "variance"
                )
                != payload.get(
                    "variance"
                ),

                existing.get(
                    "status"
                )
                != "open",
            ]
        )

        if meaningful_changed:

            changed_existing.append(
                {
                    "id":
                        existing.get(
                            "id"
                        ),

                    "payload":
                        payload,
                }
            )

        else:

            unchanged_existing_count += 1

    # --------------------------------------------------------
    # Batch insert new exceptions
    # --------------------------------------------------------

    inserted_count = 0

    for batch in chunk_list(
        new_payloads,
        EXCEPTION_BATCH_SIZE,
    ):

        if not batch:
            continue

        response = (
            supabase
            .table("exceptions")
            .insert(
                batch
            )
            .execute()
        )

        inserted_count += len(
            response.data
            or []
        )

    # --------------------------------------------------------
    # Update changed exceptions
    # --------------------------------------------------------

    updated_count = 0

    for item in changed_existing:

        exception_id = (
            item.get(
                "id"
            )
        )

        if not exception_id:
            continue

        response = (
            supabase
            .table("exceptions")
            .update(
                item[
                    "payload"
                ]
            )
            .eq(
                "id",
                exception_id,
            )
            .execute()
        )

        if response.data:

            updated_count += 1

    # --------------------------------------------------------
    # Auto-resolve conditions no longer detected
    # --------------------------------------------------------

    stale_rows = []

    for existing in existing_rows:

        fingerprint = (
            existing.get(
                "fingerprint"
            )
        )

        if not fingerprint:
            continue

        if (
            existing.get(
                "status"
            )
            != "open"
        ):
            continue

        if (
            str(fingerprint)
            in active_fingerprints
        ):
            continue

        stale_rows.append(
            existing
        )

    resolved_count = 0

    resolution_payload = {
        "status":
            "resolved",

        "resolved_at":
            now,

        "updated_at":
            now,

        "resolution_note":
            (
                "Automatically resolved because "
                "the Reality-vs-Plan condition "
                "is no longer present."
            ),
    }

    stale_ids = [
        str(row["id"])
        for row
        in stale_rows
        if row.get("id")
    ]

    for batch in chunk_list(
        stale_ids,
        EXCEPTION_BATCH_SIZE,
    ):

        if not batch:
            continue

        response = (
            supabase
            .table("exceptions")
            .update(
                resolution_payload
            )
            .in_(
                "id",
                batch,
            )
            .execute()
        )

        resolved_count += len(
            response.data
            or []
        )

    return {
        "inserted_count":
            inserted_count,

        "updated_count":
            updated_count,

        "unchanged_count":
            unchanged_existing_count,

        "auto_resolved_count":
            resolved_count,

        "active_fingerprints":
            active_fingerprints,
    }


# ============================================================
# EXCEPTION SUMMARY
# ============================================================

def build_exception_summary(
    rows: list[dict],
) -> dict:

    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    type_counts = {}

    open_count = 0

    resolved_count = 0

    for row in rows:

        row_status = (
            normalize_text(
                row.get(
                    "status"
                )
            )
        )

        if row_status == "open":

            open_count += 1

        elif row_status == "resolved":

            resolved_count += 1

        row_severity = (
            normalize_text(
                row.get(
                    "severity"
                )
            )
            or "medium"
        )

        if (
            row_severity
            not in severity_counts
        ):

            severity_counts[
                row_severity
            ] = 0

        severity_counts[
            row_severity
        ] += 1

        exception_type = (
            row.get(
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

    return {
        "total":
            len(rows),

        "open":
            open_count,

        "resolved":
            resolved_count,

        "severity_counts":
            severity_counts,

        "type_counts":
            type_counts,
    }


# ============================================================
# SEARCH HELPER
# ============================================================

def exception_matches_search(
    row: dict,
    search: str,
) -> bool:

    search_value = (
        normalize_text(
            search
        )
    )

    if not search_value:

        return True

    searchable_values = [
        row.get(
            "title"
        ),
        row.get(
            "description"
        ),
        row.get(
            "exception_type"
        ),
        row.get(
            "severity"
        ),
        row.get(
            "status"
        ),
        row.get(
            "activity_id"
        ),
        row.get(
            "source_field_event_id"
        ),
    ]

    searchable_text = " ".join(
        normalize_text(
            value
        )
        for value
        in searchable_values
        if value is not None
    )

    return (
        search_value
        in searchable_text
    )


# ============================================================
# SORT EXCEPTIONS
# ============================================================

def sort_exceptions(
    rows: list[dict],
) -> list[dict]:

    def sort_key(
        row: dict,
    ):

        severity = (
            normalize_text(
                row.get(
                    "severity"
                )
            )
        )

        severity_rank = (
            SEVERITY_RANK.get(
                severity,
                0,
            )
        )

        variance = abs(
            safe_number(
                row.get(
                    "variance"
                )
            )
        )

        detected_at = (
            row.get(
                "detected_at"
            )
            or ""
        )

        return (
            severity_rank,
            variance,
            detected_at,
        )

    return sorted(
        rows,
        key=sort_key,
        reverse=True,
    )


# ============================================================
# RUN REALITY VS PLAN ANALYSIS
# ============================================================

@router.post(
    "/analyze/{project_id}"
)
def analyze_project(
    project_id: str,
    current_user=Depends(
        get_current_user
    ),
):

    try:

        print(
            "[REALITY VS PLAN] "
            "Building current Field Twin..."
        )

        (
            twin,
            field_events,
            activity_matches,
        ) = (
            build_current_project_twin(
                project_id
            )
        )

        print(
            "[REALITY VS PLAN] "
            "Running analyzer..."
        )

        analysis = (
            analyze_project_reality_vs_plan(
                twin=twin,
                field_events=(
                    field_events
                ),
                activity_matches=(
                    activity_matches
                ),
            )
        )

        findings = (
            analysis.get(
                "exceptions"
            )
            or []
        )

        print(
            "[REALITY VS PLAN] "
            f"Generated {len(findings)} findings."
        )

        print(
            "[REALITY VS PLAN] "
            "Persisting findings in batches..."
        )

        persistence = (
            persist_exception_findings(
                project_id=project_id,
                findings=findings,
            )
        )

        print(
            "[REALITY VS PLAN] "
            "Persistence complete:",
            {
                "inserted":
                    persistence[
                        "inserted_count"
                    ],

                "updated":
                    persistence[
                        "updated_count"
                    ],

                "unchanged":
                    persistence[
                        "unchanged_count"
                    ],

                "resolved":
                    persistence[
                        "auto_resolved_count"
                    ],
            },
        )

        return {
            "message":
                (
                    "Reality-vs-Plan "
                    "analysis completed."
                ),

            "project":
                analysis.get(
                    "project"
                ),

            "generated_at":
                analysis.get(
                    "generated_at"
                ),

            "summary":
                analysis.get(
                    "summary"
                ),

            "persistence": {
                "inserted_count":
                    persistence[
                        "inserted_count"
                    ],

                "updated_count":
                    persistence[
                        "updated_count"
                    ],

                "unchanged_count":
                    persistence[
                        "unchanged_count"
                    ],

                "auto_resolved_count":
                    persistence[
                        "auto_resolved_count"
                    ],
            },

            "generated_exceptions":
                findings,
        }

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "REALITY VS PLAN ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Reality-vs-Plan analysis "
                f"failed: {str(exc)}"
            ),
        )


# ============================================================
# LIST PROJECT EXCEPTIONS
# ============================================================

@router.get(
    "/project/{project_id}"
)
def get_project_exceptions(
    project_id: str,

    status: str | None = Query(
        default=None
    ),

    exception_type: str | None = Query(
        default=None
    ),

    severity: str | None = Query(
        default=None
    ),

    search: str | None = Query(
        default=None
    ),

    page: int = Query(
        default=1,
        ge=1,
    ),

    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
    ),

    current_user=Depends(
        get_current_user
    ),
):

    try:

        project = (
            get_project(
                project_id
            )
        )

        # ----------------------------------------------------
        # CRITICAL FIX:
        #
        # Do NOT make one Supabase SELECT here.
        #
        # That was the reason the endpoint stopped at exactly
        # 1000 exceptions.
        #
        # Instead, fetch every page from Supabase.
        # ----------------------------------------------------

        all_rows = (
            get_all_project_exceptions(
                project_id
            )
        )

        print(
            "[GET EXCEPTIONS] "
            f"Database rows loaded: "
            f"{len(all_rows)}"
        )

        # ----------------------------------------------------
        # STATUS SCOPE
        #
        # Example:
        # status=open
        #
        # Summary cards should represent the entire OPEN set,
        # not merely the 25 rows shown on the current page.
        # ----------------------------------------------------

        summary_rows = all_rows

        if status:

            wanted_status = (
                normalize_text(
                    status
                )
            )

            summary_rows = [
                row
                for row
                in summary_rows
                if normalize_text(
                    row.get(
                        "status"
                    )
                )
                == wanted_status
            ]

        summary = (
            build_exception_summary(
                summary_rows
            )
        )

        # ----------------------------------------------------
        # TABLE FILTERS
        # ----------------------------------------------------

        filtered_rows = (
            summary_rows
        )

        if exception_type:

            wanted_type = (
                normalize_text(
                    exception_type
                )
            )

            filtered_rows = [
                row
                for row
                in filtered_rows
                if normalize_text(
                    row.get(
                        "exception_type"
                    )
                )
                == wanted_type
            ]

        if severity:

            wanted_severity = (
                normalize_text(
                    severity
                )
            )

            filtered_rows = [
                row
                for row
                in filtered_rows
                if normalize_text(
                    row.get(
                        "severity"
                    )
                )
                == wanted_severity
            ]

        if search:

            filtered_rows = [
                row
                for row
                in filtered_rows
                if exception_matches_search(
                    row=row,
                    search=search,
                )
            ]

        # ----------------------------------------------------
        # PRIORITY SORT
        #
        # Critical first,
        # then High,
        # Medium,
        # Low.
        #
        # Within severity, larger variance first.
        # ----------------------------------------------------

        filtered_rows = (
            sort_exceptions(
                filtered_rows
            )
        )

        # ----------------------------------------------------
        # PAGINATION
        # ----------------------------------------------------

        filtered_total = (
            len(
                filtered_rows
            )
        )

        if filtered_total == 0:

            total_pages = 0

        else:

            total_pages = math.ceil(
                filtered_total
                / page_size
            )

        start_index = (
            (page - 1)
            * page_size
        )

        end_index = (
            start_index
            + page_size
        )

        page_rows = (
            filtered_rows[
                start_index:
                end_index
            ]
        )

        has_previous = (
            page > 1
        )

        has_next = (
            page
            < total_pages
        )

        return {
            "project": {
                "id":
                    project.get(
                        "id"
                    ),

                "name":
                    project.get(
                        "name"
                    ),

                "status":
                    project.get(
                        "status"
                    ),
            },

            "summary":
                summary,

            "pagination": {
                "page":
                    page,

                "page_size":
                    page_size,

                "filtered_total":
                    filtered_total,

                "total_pages":
                    total_pages,

                "has_previous":
                    has_previous,

                "has_next":
                    has_next,
            },

            "exceptions":
                page_rows,
        }

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "GET EXCEPTIONS ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch "
                f"exceptions: {str(exc)}"
            ),
        )


# ============================================================
# GET ONE EXCEPTION
# ============================================================

@router.get(
    "/{exception_id}"
)
def get_exception(
    exception_id: str,
    current_user=Depends(
        get_current_user
    ),
):

    try:

        response = (
            supabase
            .table("exceptions")
            .select("*")
            .eq(
                "id",
                exception_id,
            )
            .limit(1)
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=404,
                detail="Exception not found",
            )

        return (
            response.data[0]
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "GET EXCEPTION ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch "
                f"exception: {str(exc)}"
            ),
        )


# ============================================================
# MANUALLY RESOLVE EXCEPTION
# ============================================================

@router.post(
    "/{exception_id}/resolve"
)
def resolve_exception(
    exception_id: str,
    payload: ResolveExceptionRequest,
    current_user=Depends(
        get_current_user
    ),
):

    try:

        existing_response = (
            supabase
            .table("exceptions")
            .select("*")
            .eq(
                "id",
                exception_id,
            )
            .limit(1)
            .execute()
        )

        if not existing_response.data:

            raise HTTPException(
                status_code=404,
                detail="Exception not found",
            )

        existing = (
            existing_response
            .data[0]
        )

        # ----------------------------------------------------
        # Already resolved
        # ----------------------------------------------------

        if (
            normalize_text(
                existing.get(
                    "status"
                )
            )
            == "resolved"
        ):

            return {
                "message":
                    (
                        "Exception is "
                        "already resolved."
                    ),

                "exception":
                    existing,
            }

        now = utc_now_iso()

        resolution_note = (
            payload.resolution_note
        )

        if (
            resolution_note
            and
            resolution_note.strip()
        ):

            resolution_note = (
                resolution_note.strip()
            )

        else:

            resolution_note = (
                "Resolved by "
                "planner/reviewer."
            )

        response = (
            supabase
            .table("exceptions")
            .update(
                {
                    "status":
                        "resolved",

                    "resolved_at":
                        now,

                    "updated_at":
                        now,

                    "resolution_note":
                        resolution_note,

                    "resolved_by":
                        current_user[
                            "id"
                        ],
                }
            )
            .eq(
                "id",
                exception_id,
            )
            .execute()
        )

        updated_exception = None

        if response.data:

            updated_exception = (
                response.data[0]
            )

        else:

            refetch = (
                supabase
                .table(
                    "exceptions"
                )
                .select("*")
                .eq(
                    "id",
                    exception_id,
                )
                .limit(1)
                .execute()
            )

            if refetch.data:

                updated_exception = (
                    refetch.data[0]
                )

        (
            supabase
            .table("audit_logs")
            .insert(
                {
                    "project_id":
                        existing.get(
                            "project_id"
                        ),

                    "user_id":
                        current_user[
                            "id"
                        ],

                    "action":
                        "exception_resolved",

                    "entity_type":
                        "exception",

                    "entity_id":
                        exception_id,

                    "old_value": {
                        "status":
                            existing.get(
                                "status"
                            ),

                        "resolution_note":
                            existing.get(
                                "resolution_note"
                            ),
                    },

                    "new_value": {
                        "status":
                            "resolved",

                        "resolution_note":
                            resolution_note,

                        "resolved_at":
                            now,

                        "activity_id":
                            existing.get(
                                "activity_id"
                            ),

                        "exception_type":
                            existing.get(
                                "exception_type"
                            ),

                        "severity":
                            existing.get(
                                "severity"
                            ),
                    },
                }
            )
            .execute()
        )

        return {
            "message":
                "Exception resolved.",

            "exception":
                updated_exception,
        }

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "RESOLVE EXCEPTION ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to resolve "
                f"exception: {str(exc)}"
            ),
        )
