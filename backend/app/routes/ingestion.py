from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.database.auth_dependency import (
    get_current_user,
)
from app.database.supabase import supabase

from ai.extraction.extractor import (
    extract_field_event,
)
from ai.parsing.parser_factory import (
    parse_input,
)


router = APIRouter(
    prefix="/ingestion",
    tags=["Multi-Format Ingestion"],
)


MAX_FILE_SIZE = 10 * 1024 * 1024


SOURCE_TYPE_MAP = {
    "txt": "text",
    "csv": "csv",
    "xlsx": "xlsx",
    "pdf": "pdf",

    "mp3": "voice",
    "wav": "voice",
    "m4a": "voice",
    "aac": "voice",
}


@router.post("/upload")
async def upload_field_input(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    ),
):
    try:
        filename = file.filename

        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file has no filename.",
            )

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=(
                    "File is too large. "
                    "Maximum size is 10 MB."
                ),
            )

        parsed_items = parse_input(
            filename=filename,
            file_bytes=file_bytes,
        )

        if not parsed_items:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No usable field information "
                    "could be extracted from the file."
                ),
            )

        reporter_id = current_user.get("id")

        if not reporter_id:
            raise HTTPException(
                status_code=401,
                detail="Authenticated user ID not found.",
            )

        extension = (
            filename.rsplit(".", 1)[-1].lower()
            if "." in filename
            else ""
        )

        source_type = SOURCE_TYPE_MAP.get(
            extension
        )

        if not source_type:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported source type: {extension}"
                ),
            )

        created_events = []

        for item in parsed_items:

            extracted = extract_field_event(
                raw_text=item.raw_text,
                discipline=item.discipline,
                area=item.area,
                quantity=item.quantity,
                unit=item.unit,
            )

            insert_payload = {
                "project_id": project_id,
                "reported_by": reporter_id,
                "source_type": source_type,
                "raw_text": item.raw_text,

                "discipline": (
                    extracted.discipline
                ),

                "area": (
                    extracted.area
                ),

                "asset_reference": (
                    extracted.asset
                ),

                "quantity": (
                    extracted.quantity
                ),

                "unit": (
                    extracted.unit
                ),

                "status": "pending",
            }

            response = (
                supabase
                .table("field_events")
                .insert(insert_payload)
                .execute()
            )

            if not response.data:
                raise RuntimeError(
                    "Failed to store parsed "
                    "field event."
                )

            event = response.data[0]

            created_events.append(
                {
                    "field_event": event,
                    "extracted": (
                        extracted.model_dump()
                    ),
                    "source_row": (
                        item.source_row
                    ),
                }
            )

        return {
            "filename": filename,
            "source_type": source_type,
            "parsed_items": len(
                parsed_items
            ),
            "created_events": (
                created_events
            ),
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Multi-format ingestion failed: "
                f"{str(exc)}"
            ),
        )