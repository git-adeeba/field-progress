import math

from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.auth_dependency import get_current_user
from app.database.supabase import supabase

router = APIRouter(prefix="/audit-trail", tags=["Audit Trail"])

DATABASE_PAGE_SIZE = 1000
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def get_project(project_id: str) -> dict:
    response = (
        supabase.table("projects")
        .select("id,name,status")
        .eq("id", project_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found.")
    return response.data[0]


def get_all_project_audit_logs(project_id: str) -> list[dict]:
    rows = []
    start = 0
    while True:
        response = (
            supabase.table("audit_logs")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .order("id", desc=True)
            .range(start, start + DATABASE_PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < DATABASE_PAGE_SIZE:
            break
        start += DATABASE_PAGE_SIZE
    return rows


def get_profiles(user_ids: set[str]) -> dict[str, dict]:
    if not user_ids:
        return {}
    response = (
        supabase.table("profiles")
        .select("id,full_name,email,role")
        .in_("id", list(user_ids))
        .execute()
    )
    return {
        str(row["id"]): row
        for row in (response.data or [])
        if row.get("id")
    }


def get_activities(activity_ids: set[str]) -> dict[str, dict]:
    if not activity_ids:
        return {}
    response = (
        supabase.table("activities")
        .select("id,activity_code,activity_name")
        .in_("id", list(activity_ids))
        .execute()
    )
    return {
        str(row["id"]): row
        for row in (response.data or [])
        if row.get("id")
    }


def extract_activity_id(row: dict) -> str | None:
    old_value = row.get("old_value") or {}
    new_value = row.get("new_value") or {}

    if row.get("entity_type") == "activity" and row.get("entity_id"):
        return str(row["entity_id"])

    value = new_value.get("activity_id") or old_value.get("activity_id")
    return str(value) if value else None


def matches_search(row: dict, search: str) -> bool:
    wanted = normalize_text(search)
    if not wanted:
        return True

    actor = row.get("actor") or {}
    activity = row.get("activity") or {}

    searchable = " ".join(
        normalize_text(value)
        for value in [
            row.get("action"),
            row.get("entity_type"),
            row.get("entity_id"),
            actor.get("full_name"),
            actor.get("email"),
            actor.get("role"),
            activity.get("activity_code"),
            activity.get("activity_name"),
            row.get("old_value"),
            row.get("new_value"),
        ]
        if value is not None
    )
    return wanted in searchable


@router.get("/project/{project_id}")
def get_project_audit_trail(
    project_id: str,
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    current_user=Depends(get_current_user),
):
    try:
        project = get_project(project_id)
        rows = get_all_project_audit_logs(project_id)

        user_ids = {
            str(row["user_id"]) for row in rows if row.get("user_id")
        }
        activity_ids = {
            activity_id
            for row in rows
            if (activity_id := extract_activity_id(row))
        }

        profiles = get_profiles(user_ids)
        activities = get_activities(activity_ids)

        enriched = []
        for row in rows:
            activity_id = extract_activity_id(row)
            enriched.append({
                **row,
                "actor": profiles.get(str(row.get("user_id")))
                    if row.get("user_id") else None,
                "activity": activities.get(activity_id)
                    if activity_id else None,
            })

        if action:
            wanted = normalize_text(action)
            enriched = [
                row for row in enriched
                if normalize_text(row.get("action")) == wanted
            ]

        if entity_type:
            wanted = normalize_text(entity_type)
            enriched = [
                row for row in enriched
                if normalize_text(row.get("entity_type")) == wanted
            ]

        if search:
            enriched = [
                row for row in enriched
                if matches_search(row, search)
            ]

        filtered_total = len(enriched)
        total_pages = (
            math.ceil(filtered_total / page_size)
            if filtered_total else 0
        )
        start = (page - 1) * page_size
        page_rows = enriched[start:start + page_size]

        action_counts = {}
        for row in rows:
            key = row.get("action") or "unknown"
            action_counts[key] = action_counts.get(key, 0) + 1

        return {
            "project": project,
            "summary": {
                "total_events": len(rows),
                "action_counts": action_counts,
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "filtered_total": filtered_total,
                "total_pages": total_pages,
                "has_previous": page > 1,
                "has_next": page < total_pages,
            },
            "audit_logs": page_rows,
        }

    except HTTPException:
        raise
    except Exception as exc:
        print("AUDIT TRAIL ERROR:", repr(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch audit trail: {str(exc)}",
        )
