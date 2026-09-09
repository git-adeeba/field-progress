from ai.matching.semantic_retriever import (
    retrieve_semantic_candidates,
)

from ai.matching.context_reconciler import (
    reconcile_candidates,
)

from ai.matching.matcher import (
    rank_activities,
)


def normalize_semantic_result(
    item: dict,
) -> dict:

    activity = (
        item.get("activity")
        or {}
    )

    return {
        "activity_id":
            activity.get("id"),

        "activity_code":
            activity.get(
                "activity_code"
            ),

        "activity_name":
            activity.get(
                "activity_name"
            )
            or activity.get("name"),

        "discipline":
            activity.get(
                "discipline"
            ),

        "area":
            activity.get(
                "area"
            ),

        "semantic_score":
            item.get(
                "semantic_score",
                0,
            ),

        "context_score":
            item.get(
                "context_score",
                0,
            ),

        "memory_bonus":
            item.get(
                "memory_bonus",
                0,
            ),

        "memory_matches":
            item.get(
                "memory_matches",
                [],
            ),

        "confidence":
            item.get(
                "confidence",
                0,
            ),

        "reason":
            item.get(
                "reason",
                (
                    "semantic "
                    "similarity"
                ),
            ),
    }


def rank_with_reconciliation(
    extracted,
    raw_text: str,
    activities: list[dict],
    top_k: int = 5,
    project_knowledge: (
        list[dict] | None
    ) = None,
) -> list[dict]:

    try:
        print(
            "[MATCHING] Starting "
            "semantic retrieval..."
        )

        semantic_candidates = (
            retrieve_semantic_candidates(
                extracted=extracted,
                activities=activities,
                top_k=10,
            )
        )

        print(
            "[MATCHING] Semantic "
            "candidates:",
            len(
                semantic_candidates
            ),
        )

        reconciled = (
            reconcile_candidates(
                extracted=extracted,
                semantic_candidates=(
                    semantic_candidates
                ),
                raw_text=raw_text,
                project_knowledge=(
                    project_knowledge
                    or []
                ),
            )
        )

        normalized = [
            normalize_semantic_result(
                item
            )
            for item
            in reconciled
        ]

        normalized = [
            item
            for item
            in normalized
            if item.get(
                "activity_id"
            )
        ]

        print(
            "[MATCHING] Context-aware "
            "reconciliation complete."
        )

        if project_knowledge:
            print(
                "[MATCHING] Project "
                "knowledge entries loaded:",
                len(
                    project_knowledge
                ),
            )

        return normalized[
            :top_k
        ]

    except Exception as exc:

        print(
            "[MATCHING] Semantic "
            "retrieval failed:",
            repr(exc),
        )

        print(
            "[MATCHING] Falling back "
            "to deterministic matcher."
        )

        extracted_data = (
            extracted.model_dump()
            if hasattr(
                extracted,
                "model_dump",
            )
            else extracted
        )

        return rank_activities(
            extracted=extracted_data,
            raw_text=raw_text,
            activities=activities,
            top_k=top_k,
        )