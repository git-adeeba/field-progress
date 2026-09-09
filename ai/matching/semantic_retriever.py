from difflib import SequenceMatcher
import re
from typing import Any


def build_activity_text(
    activity: dict[str, Any],
) -> str:

    parts = []

    for key in [
        "activity_code",
        "activity_name",
        "name",
        "discipline",
        "area",
        "wbs",
        "wbs_path",
        "description",
    ]:
        value = activity.get(key)

        if value:
            parts.append(str(value))

    return " | ".join(parts)


def build_event_text(
    extracted,
) -> str:

    parts = []

    for value in [
        extracted.work_type,
        extracted.asset,
        extracted.area,
        extracted.discipline,
        extracted.progress_state,
        extracted.remarks,
    ]:
        if value:
            parts.append(str(value))

    return " | ".join(parts)


def _normalize_text(
    value: str,
) -> str:

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def _tokens(
    value: str,
) -> set[str]:

    return {
        token
        for token in _normalize_text(
            value
        ).split()
        if len(token) > 1
    }


def _token_overlap_score(
    event_text: str,
    activity_text: str,
) -> float:

    event_tokens = _tokens(
        event_text
    )

    activity_tokens = _tokens(
        activity_text
    )

    if (
        not event_tokens
        or not activity_tokens
    ):
        return 0.0

    intersection = (
        event_tokens
        & activity_tokens
    )

    precision = (
        len(intersection)
        / len(activity_tokens)
    )

    recall = (
        len(intersection)
        / len(event_tokens)
    )

    if precision + recall == 0:
        return 0.0

    return (
        2
        * precision
        * recall
        / (precision + recall)
    ) * 100.0


def _sequence_score(
    event_text: str,
    activity_text: str,
) -> float:

    event_normalized = (
        _normalize_text(
            event_text
        )
    )

    activity_normalized = (
        _normalize_text(
            activity_text
        )
    )

    if (
        not event_normalized
        or not activity_normalized
    ):
        return 0.0

    return (
        SequenceMatcher(
            None,
            event_normalized,
            activity_normalized,
        ).ratio()
        * 100.0
    )


def _activity_code_bonus(
    event_text: str,
    activity: dict[str, Any],
) -> float:

    activity_code = activity.get(
        "activity_code"
    )

    if not activity_code:
        return 0.0

    code_parts = re.findall(
        r"[A-Za-z]+|\d+",
        str(activity_code),
    )

    if not code_parts:
        return 0.0

    pattern = (
        r"(?<![A-Za-z0-9])"
        + r"[\s_-]*".join(
            re.escape(part)
            for part in code_parts
        )
        + r"(?![A-Za-z0-9])"
    )

    if re.search(
        pattern,
        event_text,
        flags=re.IGNORECASE,
    ):
        return 100.0

    return 0.0


def _calculate_score(
    event_text: str,
    activity_text: str,
    activity: dict[str, Any],
) -> float:

    code_score = (
        _activity_code_bonus(
            event_text,
            activity,
        )
    )

    if code_score >= 100.0:
        return 98.0

    token_score = (
        _token_overlap_score(
            event_text,
            activity_text,
        )
    )

    sequence_score = (
        _sequence_score(
            event_text,
            activity_text,
        )
    )

    score = (
        token_score * 0.75
        + sequence_score * 0.25
    )

    return min(
        max(score, 0.0),
        100.0,
    )


def retrieve_semantic_candidates(
    extracted,
    activities: list[dict],
    top_k: int = 10,
) -> list[dict]:

    if not activities:
        return []

    event_text = build_event_text(
        extracted
    )

    candidates = []

    for activity in activities:

        activity_text = (
            build_activity_text(
                activity
            )
        )

        semantic_score = (
            _calculate_score(
                event_text,
                activity_text,
                activity,
            )
        )

        candidates.append(
            {
                "activity": activity,
                "semantic_score": round(
                    semantic_score,
                    2,
                ),
            }
        )

    candidates.sort(
        key=lambda candidate: (
            candidate[
                "semantic_score"
            ]
        ),
        reverse=True,
    )

    return candidates[:top_k]