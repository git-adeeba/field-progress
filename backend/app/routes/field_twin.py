from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.database.auth_dependency import (
    get_current_user,
)
from app.database.supabase import (
    supabase,
)

from ai.execution_twin.twin import (
    build_project_twin,
)


router = APIRouter(
    prefix="/field-twin",
    tags=["Field Execution Twin"],
)


# ============================================================
# FETCH ALL PROJECT ACTIVITIES
# ============================================================

def get_all_project_activities(
    project_id: str,
):
    all_activities = []

    batch_size = 1000
    start = 0

    while True:
        end = start + batch_size - 1

        response = (
            supabase
            .table("activities")
            .select("*")
            .eq(
                "project_id",
                project_id,
            )
            .range(
                start,
                end,
            )
            .execute()
        )

        rows = response.data or []

        all_activities.extend(
            rows
        )

        if len(rows) < batch_size:
            break

        start += batch_size

    return all_activities


# ============================================================
# FETCH PROJECT EXECUTION EVENTS
# ============================================================

def get_project_execution_events(
    project_id: str,
):
    response = (
        supabase
        .table("execution_events")
        .select("*")
        .eq(
            "project_id",
            project_id,
        )
        .order(
            "occurred_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


# ============================================================
# FETCH PROJECT FIELD EVENTS
# ============================================================

def get_project_field_events(
    project_id: str,
):
    response = (
        supabase
        .table("field_events")
        .select("*")
        .eq(
            "project_id",
            project_id,
        )
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


# ============================================================
# GET PROJECT FIELD EXECUTION TWIN
# ============================================================

@router.get("/{project_id}")
def get_field_twin(
    project_id: str,
    current_user=Depends(
        get_current_user
    ),
):
    try:
        # ----------------------------------------------------
        # FETCH PROJECT
        # ----------------------------------------------------

        project_response = (
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

        if not project_response.data:
            raise HTTPException(
                status_code=404,
                detail="Project not found",
            )

        project = (
            project_response.data[0]
        )

        # ----------------------------------------------------
        # FETCH OFFICIAL SCHEDULE ACTIVITIES
        # ----------------------------------------------------

        activities = (
            get_all_project_activities(
                project_id
            )
        )

        # ----------------------------------------------------
        # FETCH VERIFIED / STORED EXECUTION EVENTS
        # ----------------------------------------------------

        execution_events = (
            get_project_execution_events(
                project_id
            )
        )

        # ----------------------------------------------------
        # FETCH ORIGINAL FIELD EVIDENCE
        # ----------------------------------------------------

        field_events = (
            get_project_field_events(
                project_id
            )
        )

        # ----------------------------------------------------
        # BUILD FIELD EXECUTION TWIN V2
        # ----------------------------------------------------

        twin = build_project_twin(
            project=project,
            activities=activities,
            execution_events=execution_events,
            field_events=field_events,
        )

        return twin

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "FIELD TWIN ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to build field "
                f"execution twin: {str(exc)}"
            ),
        )