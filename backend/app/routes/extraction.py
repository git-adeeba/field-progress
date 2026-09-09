from fastapi import APIRouter, Depends, HTTPException

from app.database.auth_dependency import get_current_user
from app.database.supabase import supabase

from ai.extraction.extractor import extract_field_event


router = APIRouter(
    prefix="/extraction",
    tags=["AI Extraction"],
)


@router.post("/field-event/{field_event_id}")
def extract_event(
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

        event = response.data[0]

        extracted = extract_field_event(
            raw_text=event["raw_text"],
            discipline=event.get("discipline"),
            area=event.get("area"),
            quantity=event.get("quantity"),
            unit=event.get("unit"),
        )

        return {
            "field_event_id": field_event_id,
            "extracted": extracted.model_dump(),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(exc)}",
        )