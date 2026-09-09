from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database.auth_dependency import get_current_user
from app.database.supabase import supabase


router = APIRouter(
    prefix="/field-events",
    tags=["Field Events"],
)


class FieldEventCreate(BaseModel):
    project_id: str
    source_type: str
    raw_text: str

    event_date: Optional[datetime] = None
    discipline: Optional[str] = None
    area: Optional[str] = None
    asset_reference: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None


@router.get("")
def get_field_events(
    project_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    try:
        query = (
            supabase
            .table("field_events")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        response = (
            query
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "count": len(response.data or []),
            "field_events": response.data or [],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch field events: {str(exc)}",
        )


@router.get("/{field_event_id}")
def get_field_event(
    field_event_id: str,
    current_user=Depends(get_current_user),
):
    try:
        response = (
            supabase
            .table("field_events")
            .select("*")
            .eq("id", field_event_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Field event not found",
            )

        return response.data[0]

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch field event: {str(exc)}",
        )


@router.post("", status_code=201)
def create_field_event(
    field_event: FieldEventCreate,
    current_user=Depends(get_current_user),
):
    try:
        role = current_user["profile"]["role"]

        if role != "supervisor":
            raise HTTPException(
                status_code=403,
                detail="Only supervisors can submit field updates",
            )

        data = field_event.model_dump(exclude_none=True)

        if field_event.event_date:
            data["event_date"] = field_event.event_date.isoformat()

        # Reporter comes from verified login token.
        # The frontend/mobile app cannot choose another user.
        data["reported_by"] = current_user["id"]
        data["status"] = "pending"

        response = (
            supabase
            .table("field_events")
            .insert(data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Field event was not created",
            )

        return {
            "message": "Field event created successfully",
            "field_event": response.data[0],
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create field event: {str(exc)}",
        )