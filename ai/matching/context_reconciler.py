import re
from typing import Any


MEMORY_BONUS = 15.0

# An exact activity code is explicit schedule evidence.
# We do not lower any guardrail threshold. Instead, when a code that
# actually belongs to a candidate activity is written in the field
# update, we reflect that evidence in both retrieval/reconciliation
# scores so the existing guardrail can make a meaningful decision.
EXACT_CODE_SEMANTIC_FLOOR = 98.0
EXACT_CODE_CONTEXT_WEIGHT = 60.0


def normalize(
    value,
) -> str:
    if value is None:
        return ""

    text = str(
        value
    ).strip().lower()

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


def contains_match(
    expected,
    candidate,
) -> bool:

    a = normalize(
        expected
    )

    b = normalize(
        candidate
    )

    if not a or not b:
        return False

    return (
        a in b
        or b in a
    )


def source_term_present(
    source_term: str,
    raw_text: str,
) -> bool:

    source = normalize(
        source_term
    )

    raw = normalize(
        raw_text
    )

    if not source or not raw:
        return False

    padded_source = (
        f" {source} "
    )

    padded_raw = (
        f" {raw} "
    )

    return (
        padded_source
        in padded_raw
    )


def normalize_activity_code(
    value,
) -> str:
    """
    Normalize harmless formatting differences in schedule activity codes.

    Examples that become equivalent:
        XER-006
        XER006
        XER 006
        xer_006

    Letters and digits are preserved, so different or mistyped codes such
    as XERR006 or XER007 remain different.
    """

    if value is None:
        return ""

    return re.sub(
        r"[^A-Za-z0-9]+",
        "",
        str(value),
    ).upper()


def exact_activity_code_present(
    activity_code,
    raw_text: str,
) -> bool:

    if not activity_code:
        return False

    code_text = str(
        activity_code
    ).strip()

    if not code_text:
        return False

    # Split the schedule code into meaningful letter/number groups.
    # Example:
    #   XER-006 -> ["XER", "006"]
    #
    # Then allow harmless separators between those groups when matching
    # speech-to-text output:
    #   XER-006
    #   XER006
    #   XER 006
    #   XER_006
    #
    # The alphanumeric lookarounds keep the match strict, so XERR006,
    # XER007 and XER0060 do not qualify.
    code_parts = re.findall(
        r"[A-Za-z]+|\d+",
        code_text,
    )

    if not code_parts:
        return False

    joined_pattern = (
        r"[\s_-]*".join(
            re.escape(part)
            for part in code_parts
        )
    )

    pattern = (
        rf"(?<![A-Za-z0-9])"
        rf"{joined_pattern}"
        rf"(?![A-Za-z0-9])"
    )

    return (
        re.search(
            pattern,
            raw_text or "",
            flags=re.IGNORECASE,
        )
        is not None
    )


def build_activity_text(
    activity: dict[str, Any],
) -> str:

    return " ".join(
        str(value)
        for value in [
            activity.get(
                "activity_code"
            ),
            activity.get(
                "activity_name"
            ),
            activity.get(
                "name"
            ),
            activity.get(
                "description"
            ),
            activity.get(
                "wbs"
            ),
            activity.get(
                "wbs_path"
            ),
            activity.get(
                "area"
            ),
            activity.get(
                "discipline"
            ),
        ]
        if value
    )


def find_memory_matches(
    raw_text: str,
    activity: dict[str, Any],
    project_knowledge: list[dict],
) -> list[dict]:

    activity_text = (
        build_activity_text(
            activity
        )
    )

    matches = []

    for item in project_knowledge:

        if not item.get(
            "is_active",
            True,
        ):
            continue

        source_term = item.get(
            "source_term"
        )

        target_term = item.get(
            "target_term"
        )

        if not source_term:
            continue

        if not target_term:
            continue

        source_found = (
            source_term_present(
                source_term,
                raw_text,
            )
        )

        if not source_found:
            continue

        target_found = (
            contains_match(
                target_term,
                activity_text,
            )
        )

        if target_found:
            matches.append(
                item
            )

    return matches


def calculate_context_score(
    extracted,
    activity: dict[str, Any],
    raw_text: str = "",
) -> tuple[
    float,
    list[str],
]:

    score = 0.0
    max_score = 0.0

    reasons = []

    activity_text = (
        build_activity_text(
            activity
        )
    )

    activity_code = (
        activity.get(
            "activity_code"
        )
    )

    if exact_activity_code_present(
        activity_code,
        raw_text,
    ):
        max_score += (
            EXACT_CODE_CONTEXT_WEIGHT
        )

        score += (
            EXACT_CODE_CONTEXT_WEIGHT
        )

        reasons.append(
            "exact activity code "
            f"{activity_code}"
        )

    if extracted.work_type:
        max_score += 30

        if contains_match(
            extracted.work_type,
            activity_text,
        ):
            score += 30

            reasons.append(
                "work type match"
            )

    if extracted.asset:
        # Asset evidence should only participate in the context denominator
        # when the schedule candidate actually contains asset-level metadata
        # or text. Otherwise a correctly matched activity is penalized merely
        # because the imported schedule is less detailed than the field update.
        #
        # This keeps the guardrail strict: contradictory candidate asset data
        # still counts and can fail, while absent schedule evidence is treated
        # as unknown rather than as a mismatch.
        activity_asset = (
            activity.get("asset")
            or activity.get("asset_reference")
        )

        asset_evidence_text = (
            str(activity_asset)
            if activity_asset
            else ""
        )

        if not asset_evidence_text:
            candidate_text = normalize(
                activity_text
            )
            extracted_asset = normalize(
                extracted.asset
            )

            if (
                extracted_asset
                and extracted_asset
                in candidate_text
            ):
                asset_evidence_text = (
                    activity_text
                )

        if asset_evidence_text:
            max_score += 25

            if contains_match(
                extracted.asset,
                asset_evidence_text,
            ):
                score += 25

                reasons.append(
                    "asset match"
                )

    if extracted.area:
        max_score += 20

        activity_area = (
            activity.get("area")
            or activity_text
        )

        if contains_match(
            extracted.area,
            activity_area,
        ):
            score += 20

            reasons.append(
                "area match"
            )

    if extracted.discipline:
        max_score += 25

        activity_discipline = (
            activity.get(
                "discipline"
            )
            or activity_text
        )

        if contains_match(
            extracted.discipline,
            activity_discipline,
        ):
            score += 25

            reasons.append(
                "discipline match"
            )

    if max_score == 0:
        return (
            0.0,
            reasons,
        )

    context_score = round(
        score / max_score * 100,
        2,
    )

    return (
        context_score,
        reasons,
    )


def reconcile_candidates(
    extracted,
    semantic_candidates: list[dict],
    raw_text: str = "",
    project_knowledge: (
        list[dict] | None
    ) = None,
) -> list[dict]:

    reconciled = []

    knowledge = (
        project_knowledge
        or []
    )

    for candidate in (
        semantic_candidates
    ):

        activity = candidate[
            "activity"
        ]

        semantic_score = float(
            candidate.get(
                "semantic_score",
                0,
            )
            or 0
        )

        exact_code_match = (
            exact_activity_code_present(
                activity.get(
                    "activity_code"
                ),
                raw_text,
            )
        )

        if exact_code_match:
            semantic_score = max(
                semantic_score,
                EXACT_CODE_SEMANTIC_FLOOR,
            )

        (
            context_score,
            reasons,
        ) = (
            calculate_context_score(
                extracted,
                activity,
                raw_text=raw_text,
            )
        )

        memory_matches = (
            find_memory_matches(
                raw_text=raw_text,
                activity=activity,
                project_knowledge=(
                    knowledge
                ),
            )
        )

        memory_bonus = 0.0

        if memory_matches:
            memory_bonus = (
                MEMORY_BONUS
            )

            learned_terms = [
                (
                    f"{item.get('source_term')}"
                    " → "
                    f"{item.get('target_term')}"
                )
                for item
                in memory_matches[:3]
            ]

            reasons.append(
                "project memory: "
                + "; ".join(
                    learned_terms
                )
            )

        final_score = (
            semantic_score * 0.65
            + context_score * 0.35
            + memory_bonus
        )

        final_score = min(
            final_score,
            100.0,
        )

        reconciled.append(
            {
                "activity":
                    activity,

                "semantic_score":
                    round(
                        semantic_score,
                        2,
                    ),

                "context_score":
                    round(
                        context_score,
                        2,
                    ),

                "memory_bonus":
                    round(
                        memory_bonus,
                        2,
                    ),

                "memory_matches":
                    memory_matches,

                "confidence":
                    round(
                        final_score,
                        2,
                    ),

                "reason":
                    (
                        ", ".join(
                            reasons
                        )
                        if reasons
                        else (
                            "semantic "
                            "similarity"
                        )
                    ),
            }
        )

    reconciled.sort(
        key=lambda item:
            item["confidence"],
        reverse=True,
    )

    return reconciled
