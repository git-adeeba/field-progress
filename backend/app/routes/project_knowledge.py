from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import BaseModel

from app.database.supabase import (
    supabase_admin,
)

from app.database.auth_dependency import (
    get_current_user,
)

from app.services.project_knowledge_service import (
    create_or_increment_knowledge,
    get_project_knowledge,
)


router = APIRouter(
    prefix="/project-knowledge",
    tags=["Project Knowledge"],
)


ALLOWED_KNOWLEDGE_TYPES = {
    "alias",
    "asset_term",
    "area_term",
    "work_type_term",
    "discipline_term",
    "planner_correction",
}


class KnowledgeCreateRequest(
    BaseModel
):
    project_id: str
    knowledge_type: str
    source_term: str
    target_term: str
    source_context: str | None = None


def require_reviewer(
    current_user: dict = Depends(
        get_current_user
    ),
):
    role = (
        current_user
        .get("profile", {})
        .get("role")
    )

    if role not in [
        "planner",
        "reviewer",
    ]:
        raise HTTPException(
            status_code=403,
            detail=(
                "Planner or reviewer "
                "access required."
            ),
        )

    return current_user


@router.get(
    "/{project_id}"
)
def list_project_knowledge(
    project_id: str,
    current_user: dict = Depends(
        get_current_user
    ),
):
    knowledge = (
        get_project_knowledge(
            project_id
        )
    )

    return {
        "project_id":
            project_id,

        "count":
            len(knowledge),

        "knowledge":
            knowledge,
    }


@router.post("")
def create_project_knowledge(
    data: KnowledgeCreateRequest,
    current_user: dict = Depends(
        require_reviewer
    ),
):
    if (
        data.knowledge_type
        not in ALLOWED_KNOWLEDGE_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid knowledge type."
            ),
        )

    item = (
        create_or_increment_knowledge(
            project_id=data.project_id,
            knowledge_type=(
                data.knowledge_type
            ),
            source_term=(
                data.source_term
            ),
            target_term=(
                data.target_term
            ),
            source_context=(
                data.source_context
            ),
            created_by=(
                current_user["id"]
            ),
            confidence=1.0,
        )
    )

    if not item:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to create "
                "project knowledge."
            ),
        )

    return item


@router.delete(
    "/{knowledge_id}"
)
def deactivate_project_knowledge(
    knowledge_id: str,
    current_user: dict = Depends(
        require_reviewer
    ),
):
    response = (
        supabase_admin
        .table("project_knowledge")
        .update(
            {
                "is_active":
                    False
            }
        )
        .eq(
            "id",
            knowledge_id,
        )
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail=(
                "Project knowledge "
                "not found."
            ),
        )

    return {
        "message":
            "Project knowledge deactivated.",

        "knowledge":
            response.data[0],
    }