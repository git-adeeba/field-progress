from functools import lru_cache
from typing import Any

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(
        MODEL_NAME
    )


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
            parts.append(
                str(value)
            )

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
            parts.append(
                str(value)
            )

    return " | ".join(parts)


def retrieve_semantic_candidates(
    extracted,
    activities: list[dict],
    top_k: int = 10,
) -> list[dict]:

    if not activities:
        return []

    model = get_embedding_model()

    event_text = build_event_text(
        extracted
    )

    activity_texts = [
        build_activity_text(activity)
        for activity in activities
    ]

    event_embedding = model.encode(
        event_text,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )

    activity_embeddings = model.encode(
        activity_texts,
        convert_to_tensor=True,
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=False,
    )

    scores = cos_sim(
        event_embedding,
        activity_embeddings,
    )[0]

    ranked_indices = (
        scores
        .argsort(
            descending=True
        )
        .tolist()
    )

    candidates = []

    for index in ranked_indices[:top_k]:

        activity = activities[index]

        candidates.append(
            {
                "activity": activity,
                "semantic_score": round(
                    float(
                        scores[index]
                    ) * 100,
                    2,
                ),
            }
        )

    return candidates