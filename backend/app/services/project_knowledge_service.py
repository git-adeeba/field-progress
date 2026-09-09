import re
from typing import Any

from app.database.supabase import supabase_admin
from ai.extraction.extractor import extract_field_event


GENERIC_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "today",
    "yesterday",
    "tomorrow",
    "work",
    "activity",
    "done",
    "completed",
    "complete",
    "started",
    "start",
    "finished",
    "finish",
    "progress",
    "area",
    "ongoing",
    "currently",
    "percent",
    "percentage",
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def tokenize(value: Any) -> list[str]:
    normalized = normalize_text(value)

    if not normalized:
        return []

    return normalized.split()


# -------------------------------------------------------------------
# Noise filtering for learned terminology
# -------------------------------------------------------------------

def is_valid_knowledge_token(
    token: str,
) -> bool:
    """
    Returns True only when a token is reasonable terminology
    that could potentially be learned as project knowledge.

    Prevents percentages, quantities, dates and numeric noise
    from becoming aliases.
    """

    if not token:
        return False

    token = token.strip().lower()

    if not token:
        return False

    # ---------------------------------------------------------------
    # Pure numbers
    #
    # Examples:
    # 45
    # 100
    # 2026
    # ---------------------------------------------------------------

    if token.isdigit():
        return False

    # ---------------------------------------------------------------
    # Decimal numbers
    #
    # Examples:
    # 45.5
    # 100.25
    # ---------------------------------------------------------------

    if re.fullmatch(
        r"\d+(?:\.\d+)?",
        token,
    ):
        return False

    # ---------------------------------------------------------------
    # Percentage-like values
    #
    # normalize_text removes %, but keep this protection
    # for future callers as well.
    # ---------------------------------------------------------------

    if re.fullmatch(
        r"\d+(?:\.\d+)?%",
        token,
    ):
        return False

    # ---------------------------------------------------------------
    # Date-like values
    #
    # Examples:
    # 06-09-2026
    # 2026/09/06
    # ---------------------------------------------------------------

    if re.fullmatch(
        r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}",
        token,
    ):
        return False

    # ---------------------------------------------------------------
    # Require at least one alphabetic character.
    #
    # This still allows useful abbreviations such as:
    # PH
    # TK1
    # P101
    #
    # but rejects:
    # 45
    # 2026
    # ---------------------------------------------------------------

    if not re.search(
        r"[a-z]",
        token,
    ):
        return False

    return True


def clean_knowledge_tokens(
    tokens: list[str],
) -> list[str]:

    cleaned = []

    for token in tokens:

        token = (
            token
            .strip()
            .lower()
        )

        if not is_valid_knowledge_token(
            token
        ):
            continue

        if token in GENERIC_STOPWORDS:
            continue

        cleaned.append(
            token
        )

    return cleaned


# -------------------------------------------------------------------
# Project knowledge retrieval
# -------------------------------------------------------------------

def get_project_knowledge(
    project_id: str,
) -> list[dict]:

    response = (
        supabase_admin
        .table(
            "project_knowledge"
        )
        .select("*")
        .eq(
            "project_id",
            project_id,
        )
        .eq(
            "is_active",
            True,
        )
        .order(
            "created_at"
        )
        .execute()
    )

    return (
        response.data
        or []
    )


# -------------------------------------------------------------------
# Create / reuse knowledge
# -------------------------------------------------------------------

def create_or_increment_knowledge(
    project_id: str,
    knowledge_type: str,
    source_term: str,
    target_term: str,
    created_by: str | None = None,
    source_context: str | None = None,
    field_event_id: str | None = None,
    match_id: str | None = None,
    confidence: float = 1.0,
) -> dict | None:

    source_term = (
        source_term.strip()
    )

    target_term = (
        target_term.strip()
    )

    if (
        not source_term
        or not target_term
    ):
        return None

    # ---------------------------------------------------------------
    # Additional protection specifically for aliases.
    #
    # Even if another caller creates an alias in the future,
    # numeric garbage should not reach the DB.
    # ---------------------------------------------------------------

    if knowledge_type == "alias":

        source_tokens = tokenize(
            source_term
        )

        if not source_tokens:
            return None

        valid_source_tokens = (
            clean_knowledge_tokens(
                source_tokens
            )
        )

        if not valid_source_tokens:
            return None

        # Reject if cleaning removed part of the candidate.
        # This prevents things such as:
        #
        # "45 ph"
        #
        # from silently becoming:
        #
        # "ph"
        #
        # at this layer.
        #
        # Alias inference should produce a clean candidate itself.

        if (
            len(valid_source_tokens)
            != len(source_tokens)
        ):
            return None

    existing_response = (
        supabase_admin
        .table(
            "project_knowledge"
        )
        .select("*")
        .eq(
            "project_id",
            project_id,
        )
        .eq(
            "knowledge_type",
            knowledge_type,
        )
        .eq(
            "is_active",
            True,
        )
        .execute()
    )

    existing_rows = (
        existing_response.data
        or []
    )

    normalized_source = (
        normalize_text(
            source_term
        )
    )

    normalized_target = (
        normalize_text(
            target_term
        )
    )

    for row in existing_rows:

        if (
            normalize_text(
                row.get(
                    "source_term"
                )
            )
            == normalized_source

            and

            normalize_text(
                row.get(
                    "target_term"
                )
            )
            == normalized_target
        ):

            usage_count = int(
                row.get(
                    "usage_count"
                )
                or 0
            )

            update_response = (
                supabase_admin
                .table(
                    "project_knowledge"
                )
                .update(
                    {
                        "usage_count":
                            usage_count + 1,
                    }
                )
                .eq(
                    "id",
                    row["id"],
                )
                .execute()
            )

            if update_response.data:
                return (
                    update_response
                    .data[0]
                )

            return row

    payload = {
        "project_id":
            project_id,

        "knowledge_type":
            knowledge_type,

        "source_term":
            source_term,

        "target_term":
            target_term,

        "source_context":
            source_context,

        "confidence":
            confidence,

        "learned_from_field_event_id":
            field_event_id,

        "learned_from_match_id":
            match_id,

        "created_by":
            created_by,

        "usage_count":
            0,

        "is_active":
            True,
    }

    insert_response = (
        supabase_admin
        .table(
            "project_knowledge"
        )
        .insert(
            payload
        )
        .execute()
    )

    if insert_response.data:
        return (
            insert_response
            .data[0]
        )

    return None


# -------------------------------------------------------------------
# Extract possible unknown field terminology
# -------------------------------------------------------------------

def extract_unknown_source_terms(
    raw_text: str,
    extracted,
) -> list[str]:

    raw_tokens = tokenize(
        raw_text
    )

    excluded = set(
        GENERIC_STOPWORDS
    )

    extracted_values = [
        getattr(
            extracted,
            "work_type",
            None,
        ),

        getattr(
            extracted,
            "asset",
            None,
        ),

        getattr(
            extracted,
            "area",
            None,
        ),

        getattr(
            extracted,
            "discipline",
            None,
        ),

        getattr(
            extracted,
            "progress_state",
            None,
        ),

        # -----------------------------------------------------------
        # IMPORTANT:
        # Physical progress information must NEVER become aliases.
        # -----------------------------------------------------------

        getattr(
            extracted,
            "progress_percent",
            None,
        ),

        getattr(
            extracted,
            "quantity",
            None,
        ),

        getattr(
            extracted,
            "unit",
            None,
        ),

        getattr(
            extracted,
            "quantity_mode",
            None,
        ),
    ]

    for value in extracted_values:

        excluded.update(
            tokenize(value)
        )

    remaining = []

    for token in raw_tokens:

        if token in excluded:
            continue

        if not is_valid_knowledge_token(
            token
        ):
            continue

        remaining.append(
            token
        )

    return remaining


# -------------------------------------------------------------------
# Extract meaningful target terminology from approved activity
# -------------------------------------------------------------------

def extract_target_asset_terms(
    activity: dict,
    extracted,
) -> list[str]:

    activity_name = (
        activity.get(
            "activity_name"
        )
        or activity.get("name")
        or ""
    )

    tokens = tokenize(
        activity_name
    )

    excluded = set(
        GENERIC_STOPWORDS
    )

    work_type = getattr(
        extracted,
        "work_type",
        None,
    )

    excluded.update(
        tokenize(
            work_type
        )
    )

    remaining = []

    for token in tokens:

        if token in excluded:
            continue

        if not is_valid_knowledge_token(
            token
        ):
            continue

        remaining.append(
            token
        )

    return remaining


# -------------------------------------------------------------------
# Infer alias from planner correction
# -------------------------------------------------------------------

def infer_alias_from_correction(
    raw_text: str,
    activity: dict,
    extracted,
) -> tuple[str, str] | None:

    source_tokens = (
        extract_unknown_source_terms(
            raw_text=raw_text,
            extracted=extracted,
        )
    )

    target_tokens = (
        extract_target_asset_terms(
            activity=activity,
            extracted=extracted,
        )
    )

    if not source_tokens:
        return None

    if not target_tokens:
        return None

    # Avoid learning whole sentences as aliases.
    if len(source_tokens) > 3:
        return None

    if len(target_tokens) > 4:
        return None

    source_term = " ".join(
        source_tokens
    )

    target_term = " ".join(
        target_tokens
    )

    # ---------------------------------------------------------------
    # Final alias safety check
    # ---------------------------------------------------------------

    source_term_tokens = tokenize(
        source_term
    )

    if not source_term_tokens:
        return None

    for token in source_term_tokens:

        if not is_valid_knowledge_token(
            token
        ):
            return None

    normalized_source = (
        normalize_text(
            source_term
        )
    )

    normalized_target = (
        normalize_text(
            target_term
        )
    )

    if (
        not normalized_source
        or not normalized_target
    ):
        return None

    if (
        normalized_source
        == normalized_target
    ):
        return None

    if (
        normalized_source
        in normalized_target
    ):
        return None

    return (
        source_term,
        target_term,
    )


# -------------------------------------------------------------------
# Learn from human-approved correction
# -------------------------------------------------------------------

def learn_from_planner_correction(
    event: dict,
    approved_match: dict,
    current_user_id: str,
) -> list[dict]:

    learned_items = []

    project_id = event[
        "project_id"
    ]

    activity_id = approved_match[
        "activity_id"
    ]

    activity_response = (
        supabase_admin
        .table(
            "activities"
        )
        .select("*")
        .eq(
            "id",
            activity_id,
        )
        .limit(1)
        .execute()
    )

    if not activity_response.data:
        return []

    activity = (
        activity_response
        .data[0]
    )

    raw_text = (
        event.get(
            "raw_text"
        )
        or ""
    )

    activity_name = (
        activity.get(
            "activity_name"
        )
        or activity.get("name")
        or ""
    )

    if (
        not raw_text
        or not activity_name
    ):
        return []

    extracted = (
        extract_field_event(
            raw_text
        )
    )

    # ---------------------------------------------------------------
    # Store planner-confirmed mapping
    # ---------------------------------------------------------------

    correction_memory = (
        create_or_increment_knowledge(
            project_id=project_id,

            knowledge_type=(
                "planner_correction"
            ),

            source_term=raw_text,

            target_term=activity_name,

            created_by=(
                current_user_id
            ),

            source_context=(
                "Planner-confirmed "
                "field-event to schedule "
                "activity mapping."
            ),

            field_event_id=event[
                "id"
            ],

            match_id=approved_match[
                "id"
            ],

            confidence=1.0,
        )
    )

    if correction_memory:

        learned_items.append(
            correction_memory
        )

    # ---------------------------------------------------------------
    # Infer project-specific alias
    # ---------------------------------------------------------------

    inferred_alias = (
        infer_alias_from_correction(
            raw_text=raw_text,
            activity=activity,
            extracted=extracted,
        )
    )

    if inferred_alias:

        (
            source_term,
            target_term,
        ) = inferred_alias

        alias_memory = (
            create_or_increment_knowledge(
                project_id=project_id,

                knowledge_type="alias",

                source_term=(
                    source_term
                ),

                target_term=(
                    target_term
                ),

                created_by=(
                    current_user_id
                ),

                source_context=(
                    "Automatically inferred "
                    "from a planner-confirmed "
                    "activity correction."
                ),

                field_event_id=event[
                    "id"
                ],

                match_id=approved_match[
                    "id"
                ],

                confidence=1.0,
            )
        )

        if alias_memory:

            learned_items.append(
                alias_memory
            )

    # ---------------------------------------------------------------
    # Learn area terminology
    # ---------------------------------------------------------------

    extracted_area = getattr(
        extracted,
        "area",
        None,
    )

    activity_area = (
        activity.get(
            "area"
        )
    )

    if (
        extracted_area
        and activity_area

        and normalize_text(
            extracted_area
        )
        != normalize_text(
            activity_area
        )

        and normalize_text(
            extracted_area
        )
        not in normalize_text(
            activity_area
        )
    ):

        area_memory = (
            create_or_increment_knowledge(
                project_id=project_id,

                knowledge_type=(
                    "area_term"
                ),

                source_term=(
                    extracted_area
                ),

                target_term=(
                    activity_area
                ),

                created_by=(
                    current_user_id
                ),

                source_context=(
                    "Area terminology learned "
                    "from planner-confirmed "
                    "activity mapping."
                ),

                field_event_id=event[
                    "id"
                ],

                match_id=approved_match[
                    "id"
                ],

                confidence=1.0,
            )
        )

        if area_memory:

            learned_items.append(
                area_memory
            )

    return learned_items