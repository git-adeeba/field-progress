from types import SimpleNamespace

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel

from app.database.auth_dependency import (
    get_current_user,
)

from app.database.supabase import (
    supabase,
)

from app.routes.matches import (
    generate_activity_matches,
)

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


class TextFieldInput(BaseModel):
    project_id: str
    text: str


def _process_parsed_items(
    *,
    project_id: str,
    filename: str,
    source_type: str,
    parsed_items,
    current_user,
):
    reporter_id = (
        current_user.get("id")
    )

    created_events = []

    matched_count = 0
    review_required_count = 0
    auto_verified_count = 0
    matching_failed_count = 0

    for item in parsed_items:
        # -----------------------------------------------------------
        # Extract structured evidence ONCE
        # -----------------------------------------------------------

        extracted = (
            extract_field_event(
                raw_text=item.raw_text,
                discipline=getattr(
                    item,
                    "discipline",
                    None,
                ),
                area=getattr(
                    item,
                    "area",
                    None,
                ),
                quantity=getattr(
                    item,
                    "quantity",
                    None,
                ),
                unit=getattr(
                    item,
                    "unit",
                    None,
                ),
            )
        )

        extracted_dict = (
            extracted.model_dump()
        )

        # -----------------------------------------------------------
        # Persist field event + structured extraction.
        #
        # matches.py reuses field_events.extracted_data when present,
        # so matching does NOT ask Gemini to interpret the same
        # evidence a second time.
        # -----------------------------------------------------------

        insert_payload = {
            "project_id":
                project_id,

            "reported_by":
                reporter_id,

            "source_type":
                source_type,

            "raw_text":
                item.raw_text,

            "discipline":
                extracted.discipline,

            "area":
                extracted.area,

            "asset_reference":
                extracted.asset,

            "quantity":
                extracted.quantity,

            "unit":
                extracted.unit,

            "status":
                "pending",

            "extracted_data":
                extracted_dict,
        }

        try:
            response = (
                supabase
                .table("field_events")
                .insert(
                    insert_payload
                )
                .execute()
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to save a field "
                    f"update: {exc}"
                ),
            ) from exc

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Field update insert "
                    "returned no data."
                ),
            )

        event = (
            response.data[0]
        )

        # -----------------------------------------------------------
        # Immediately run activity matching.
        #
        # matches.py decides whether:
        # - confidence is high enough to auto-verify, OR
        # - planner review is required.
        #
        # One failed match must NOT throw away the successfully
        # persisted field update.
        # -----------------------------------------------------------

        matching_result = None
        matching_error = None

        try:
            matching_result = (
                generate_activity_matches(
                    field_event_id=(
                        event["id"]
                    ),
                    current_user=(
                        current_user
                    ),
                )
            )

            matched_count += 1

            execution_event = (
                matching_result
                .get(
                    "execution_event"
                )
            )

            if execution_event:
                auto_verified_count += 1
            else:
                review_required_count += 1

        except Exception as exc:
            matching_failed_count += 1
            matching_error = str(exc)

            print(
                "[INGESTION MATCHING] "
                "Matching failed for "
                f"{event['id']}: "
                f"{matching_error}"
            )

        created_events.append(
            {
                "field_event":
                    event,

                "extracted":
                    extracted_dict,

                "source_row":
                    getattr(
                        item,
                        "source_row",
                        None,
                    ),

                "matching":
                    matching_result,

                "matching_error":
                    matching_error,
            }
        )

    return {
        "filename":
            filename,

        "source_type":
            source_type,

        "parsed_items":
            len(parsed_items),

        "created_events":
            created_events,

        "matching_summary": {
            "processed":
                matched_count,

            "auto_verified":
                auto_verified_count,

            "review_required":
                review_required_count,

            "failed":
                matching_failed_count,
        },
    }


@router.post("/upload")
async def upload_field_input(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    ),
):
    filename = (
        file.filename
        or "field-update"
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
                "Uploaded file exceeds "
                "the 10 MB limit."
            ),
        )

    extension = ""

    if "." in filename:
        extension = (
            filename
            .rsplit(".", 1)[-1]
            .lower()
        )

    source_type = (
        SOURCE_TYPE_MAP
        .get(extension)
    )

    if not source_type:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported field input "
                f"type: .{extension}"
            ),
        )

    try:
        parsed_items = parse_input(
            filename=filename,
            file_bytes=file_bytes,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Could not parse uploaded "
                f"file: {exc}"
            ),
        ) from exc

    if not parsed_items:
        raise HTTPException(
            status_code=422,
            detail=(
                "No field updates could be "
                "extracted from this file."
            ),
        )

    return _process_parsed_items(
        project_id=project_id,
        filename=filename,
        source_type=source_type,
        parsed_items=parsed_items,
        current_user=current_user,
    )


@router.post("/text")
async def ingest_typed_field_update(
    payload: TextFieldInput = Body(...),
    current_user=Depends(
        get_current_user
    ),
):
    project_id = (
        payload.project_id
        .strip()
    )

    raw_text = (
        payload.text
        .strip()
    )

    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Project ID is required.",
        )

    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail=(
                "Field update text cannot "
                "be empty."
            ),
        )

    if len(
        raw_text.encode(
            "utf-8"
        )
    ) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "Typed field update exceeds "
                "the 10 MB limit."
            ),
        )

    parsed_items = [
        SimpleNamespace(
            raw_text=raw_text,
            discipline=None,
            area=None,
            quantity=None,
            unit=None,
            source_row=1,
        )
    ]

    return _process_parsed_items(
        project_id=project_id,
        filename="typed-field-update.txt",
        source_type="text",
        parsed_items=parsed_items,
        current_user=current_user,
    )
