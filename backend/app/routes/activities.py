from fastapi import APIRouter, HTTPException

from app.database.supabase import supabase


router = APIRouter(
    prefix="/projects",
    tags=["Activities"],
)


@router.get("/{project_id}/activities")
def get_project_activities(project_id: str):
    try:
        all_activities = []
        page_size = 1000
        start = 0

        while True:
            response = (
                supabase
                .table("activities")
                .select(
                    "id,"
                    "project_id,"
                    "activity_code,"
                    "activity_name,"
                    "wbs_level,"
                    "discipline,"
                    "area,"
                    "planned_start,"
                    "planned_finish,"
                    "actual_start,"
                    "actual_finish,"
                    "planned_progress,"
                    "actual_progress,"
                    "status"
                )
                .eq("project_id", project_id)
                .order("activity_code")
                .range(start, start + page_size - 1)
                .execute()
            )

            batch = response.data or []
            all_activities.extend(batch)

            if len(batch) < page_size:
                break

            start += page_size

        return {
            "count": len(all_activities),
            "activities": all_activities,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch activities: {str(exc)}",
        )