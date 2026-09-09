from fastapi import (
    APIRouter,
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

from app.services.schedule_import_service import (
    clear_project_schedule,
    import_schedule,
    preview_schedule_import,
)


router = APIRouter(
    prefix="/schedule-import",
    tags=["Schedule Import"],
)


MAX_FILE_SIZE = (
    50
    * 1024
    * 1024
)


SUPPORTED_SUFFIXES = (
    ".csv",
    ".xlsx",
    ".xer",
)


async def read_schedule_file(
    file: UploadFile,
) -> bytes:

    filename = (
        file.filename
        or ""
    )

    lower_name = (
        filename.lower()
    )

    if not lower_name.endswith(
        SUPPORTED_SUFFIXES
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported schedule file. "
                "Supported formats: "
                "Primavera P6 XER, XLSX and CSV."
            ),
        )

    file_bytes = (
        await file.read()
    )

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file is empty."
            ),
        )

    if (
        len(file_bytes)
        > MAX_FILE_SIZE
    ):

        raise HTTPException(
            status_code=413,
            detail=(
                "Schedule file is too large. "
                "Maximum size is 50 MB."
            ),
        )

    return file_bytes


@router.post(
    "/preview"
)
async def preview_schedule(
    project_id: str = Form(...),
    file: UploadFile = File(...),
):

    try:

        file_bytes = (
            await read_schedule_file(
                file
            )
        )

        return preview_schedule_import(
            project_id=project_id,
            filename=(
                file.filename
                or "schedule"
            ),
            file_bytes=file_bytes,
        )

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
                "Failed to preview "
                f"schedule: {str(exc)}"
            ),
        )


@router.post(
    "/confirm"
)
async def confirm_schedule_import(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    ),
):

    try:

        file_bytes = (
            await read_schedule_file(
                file
            )
        )

        filename = (
            file.filename
            or "schedule"
        )

        result = import_schedule(
            project_id=project_id,
            filename=filename,
            file_bytes=file_bytes,
        )

        (
            supabase
            .table("audit_logs")
            .insert(
                {
                    "project_id":
                        project_id,

                    "user_id":
                        current_user[
                            "id"
                        ],

                    "action":
                        "schedule_imported",

                    "entity_type":
                        "schedule",

                    "entity_id":
                        project_id,

                    "old_value":
                        None,

                    "new_value": {
                        "filename":
                            filename,

                        "format":
                            (
                                filename
                                .rsplit(
                                    ".",
                                    1,
                                )[-1]
                                .lower()
                                if "."
                                in filename
                                else "unknown"
                            ),

                        "summary":
                            result.get(
                                "summary",
                                {}
                            ),

                        "warnings":
                            result.get(
                                "warnings",
                                []
                            ),
                    },
                }
            )
            .execute()
        )

        return result

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
                "Failed to import "
                f"schedule: {str(exc)}"
            ),
        )


class ClearScheduleRequest(BaseModel):
    project_id: str


@router.post(
    "/clear"
)
def clear_schedule(
    payload: ClearScheduleRequest,
    current_user=Depends(
        get_current_user
    ),
):
    try:
        result = clear_project_schedule(
            project_id=payload.project_id,
        )

        (
            supabase
            .table("audit_logs")
            .insert(
                {
                    "project_id":
                        payload.project_id,

                    "user_id":
                        current_user[
                            "id"
                        ],

                    "action":
                        "schedule_cleared",

                    "entity_type":
                        "schedule",

                    "entity_id":
                        payload.project_id,

                    "old_value": {
                        "schedule_present":
                            True,
                    },

                    "new_value": {
                        "schedule_present":
                            False,

                        "summary":
                            result.get(
                                "summary",
                                {}
                            ),
                    },
                }
            )
            .execute()
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to clear schedule: "
                f"{str(exc)}"
            ),
        )
