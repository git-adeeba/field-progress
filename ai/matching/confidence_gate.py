from typing import Any


AUTO_CONFIDENCE_THRESHOLD = 85.0
MIN_MARGIN = 10.0
MIN_CONTEXT_SCORE = 75.0
MIN_SEMANTIC_SCORE = 65.0


def evaluate_match_guardrail(
    ranked_matches: list[dict[str, Any]],
) -> dict[str, Any]:

    if not ranked_matches:
        return {
            "decision": "REVIEW_REQUIRED",
            "auto_verify": False,
            "reason": "No candidate matches were produced.",
            "top_confidence": 0.0,
            "second_confidence": 0.0,
            "margin": 0.0,
            "semantic_score": 0.0,
            "context_score": 0.0,
            "checks": {},
        }

    top_match = ranked_matches[0]

    top_confidence = float(
        top_match.get("confidence", 0) or 0
    )

    semantic_score = float(
        top_match.get("semantic_score", 0) or 0
    )

    context_score = float(
        top_match.get("context_score", 0) or 0
    )

    second_confidence = 0.0

    if len(ranked_matches) > 1:
        second_confidence = float(
            ranked_matches[1].get(
                "confidence",
                0,
            )
            or 0
        )

    margin = round(
        top_confidence - second_confidence,
        2,
    )

    checks = {
        "confidence_passed":
            top_confidence >= AUTO_CONFIDENCE_THRESHOLD,

        "margin_passed":
            margin >= MIN_MARGIN,

        "context_passed":
            context_score >= MIN_CONTEXT_SCORE,

        "semantic_passed":
            semantic_score >= MIN_SEMANTIC_SCORE,
    }

    auto_verify = all(
        checks.values()
    )

    if auto_verify:
        decision = "AUTO_VERIFIED"
        reason = (
            "Top candidate passed confidence, "
            "margin, semantic and context guardrails."
        )
    else:
        decision = "REVIEW_REQUIRED"

        failed = [
            name
            for name, passed
            in checks.items()
            if not passed
        ]

        reason = (
            "Guardrail failed: "
            + ", ".join(failed)
        )

    return {
        "decision": decision,
        "auto_verify": auto_verify,
        "reason": reason,

        "top_confidence":
            round(top_confidence, 2),

        "second_confidence":
            round(second_confidence, 2),

        "margin":
            margin,

        "semantic_score":
            round(semantic_score, 2),

        "context_score":
            round(context_score, 2),

        "thresholds": {
            "confidence":
                AUTO_CONFIDENCE_THRESHOLD,

            "margin":
                MIN_MARGIN,

            "context":
                MIN_CONTEXT_SCORE,

            "semantic":
                MIN_SEMANTIC_SCORE,
        },

        "checks":
            checks,
    }
    