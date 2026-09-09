from fastapi import APIRouter, HTTPException

from app.database.supabase import supabase


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.get("")
def get_projects():
    try:
        response = (
            supabase
            .table("projects")
            .select("id,name,description,start_date,end_date,status,created_at")
            .order("name")
            .execute()
        )

        return {
            "count": len(response.data),
            "projects": response.data,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch projects: {str(exc)}",
        )