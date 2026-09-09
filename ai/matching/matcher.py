import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional


STOP_WORDS = {
    "the",
    "a",
    "an",
    "for",
    "of",
    "in",
    "on",
    "at",
    "to",
    "and",
    "with",
    "work",
    "works",
    "activity",
}


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"[^a-z0-9\s-]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def tokenize(value: Optional[str]) -> set[str]:
    text = normalize_text(value)

    return {
        token
        for token in text.split()
        if token not in STOP_WORDS and len(token) > 1
    }


def token_similarity(source: str, target: str) -> float:
    source_tokens = tokenize(source)
    target_tokens = tokenize(target)

    if not source_tokens or not target_tokens:
        return 0.0

    overlap = source_tokens.intersection(target_tokens)

    return len(overlap) / len(source_tokens)


def sequence_similarity(source: str, target: str) -> float:
    source = normalize_text(source)
    target = normalize_text(target)

    if not source or not target:
        return 0.0

    return SequenceMatcher(
        None,
        source,
        target,
    ).ratio()


def contains_context(
    expected: Optional[str],
    candidate: Optional[str],
) -> bool:
    expected_text = normalize_text(expected)
    candidate_text = normalize_text(candidate)

    if not expected_text or not candidate_text:
        return False

    return (
        expected_text in candidate_text
        or candidate_text in expected_text
    )


def match_activity(
    extracted: Dict[str, Any],
    raw_text: str,
    activity: Dict[str, Any],
) -> Dict[str, Any]:

    activity_name = activity.get("activity_name", "")
    activity_code = activity.get("activity_code", "")
    activity_discipline = activity.get("discipline")
    activity_area = activity.get("area")

    work_type = extracted.get("work_type")
    asset = extracted.get("asset")
    event_area = extracted.get("area")
    event_discipline = extracted.get("discipline")

    activity_text = " ".join(
        [
            str(activity_code or ""),
            str(activity_name or ""),
            str(activity_discipline or ""),
            str(activity_area or ""),
        ]
    )

    event_text = " ".join(
        filter(
            None,
            [
                raw_text,
                work_type,
                asset,
                event_area,
                event_discipline,
            ],
        )
    )

    reasons: List[str] = []

    # -----------------------------
    # Text similarity
    # -----------------------------

    token_score = token_similarity(
        event_text,
        activity_text,
    )

    sequence_score = sequence_similarity(
        raw_text,
        activity_name,
    )

    text_similarity = (
        token_score * 0.75
        + sequence_score * 0.25
    )

    # Maximum contribution = 45
    text_points = text_similarity * 45

    if token_score >= 0.25:
        reasons.append("Field wording overlaps with activity description")

    # -----------------------------
    # Work type
    # Maximum contribution = 20
    # -----------------------------

    work_points = 0.0

    if work_type:
        work_tokens = tokenize(work_type)
        activity_tokens = tokenize(activity_text)

        if work_tokens.intersection(activity_tokens):
            work_points = 20.0
            reasons.append(
                f"Work type '{work_type}' matches activity"
            )

    # -----------------------------
    # Asset
    # Maximum contribution = 15
    # -----------------------------

    asset_points = 0.0

    if asset:
        asset_tokens = tokenize(asset)
        activity_tokens = tokenize(activity_text)

        if asset_tokens and asset_tokens.issubset(activity_tokens):
            asset_points = 15.0
            reasons.append(
                f"Asset '{asset}' matches activity"
            )
        elif asset_tokens.intersection(activity_tokens):
            asset_points = 8.0
            reasons.append(
                f"Activity partially matches asset '{asset}'"
            )

    # -----------------------------
    # Area
    # Maximum contribution = 10
    # -----------------------------

    area_points = 0.0

    if event_area and activity_area:
        if contains_context(event_area, activity_area):
            area_points = 10.0
            reasons.append(
                f"Area matches '{activity_area}'"
            )
        else:
            event_area_tokens = tokenize(event_area)
            activity_area_tokens = tokenize(activity_area)

            if event_area_tokens.intersection(activity_area_tokens):
                area_points = 5.0
                reasons.append(
                    "Area partially matches"
                )

    # -----------------------------
    # Discipline
    # Maximum contribution = 10
    # -----------------------------

    discipline_points = 0.0

    if event_discipline and activity_discipline:
        if normalize_text(event_discipline) == normalize_text(
            activity_discipline
        ):
            discipline_points = 10.0
            reasons.append(
                f"Discipline matches '{activity_discipline}'"
            )

    final_score = (
        text_points
        + work_points
        + asset_points
        + area_points
        + discipline_points
    )

    final_score = min(
        round(final_score, 2),
        100.0,
    )

    # Separate scores kept because our DB already
    # has semantic_score + context_score columns.
    semantic_score = round(
        text_similarity * 100,
        2,
    )

    context_score = round(
        (
            work_points
            + asset_points
            + area_points
            + discipline_points
        )
        / 55
        * 100,
        2,
    )

    if not reasons:
        reasons.append(
            "Candidate selected from general wording similarity"
        )

    return {
        "activity_id": activity.get("id"),
        "activity_code": activity_code,
        "activity_name": activity_name,
        "discipline": activity_discipline,
        "area": activity_area,
        "confidence": final_score,
        "semantic_score": semantic_score,
        "context_score": context_score,
        "reason": "; ".join(reasons),
    }


def rank_activities(
    extracted: Dict[str, Any],
    raw_text: str,
    activities: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:

    matches = [
        match_activity(
            extracted=extracted,
            raw_text=raw_text,
            activity=activity,
        )
        for activity in activities
    ]

    matches.sort(
        key=lambda item: item["confidence"],
        reverse=True,
    )

    return matches[:top_k]