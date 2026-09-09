from ai.parsing.models import ParsedInputItem


def parse_text(content: str) -> list[ParsedInputItem]:
    cleaned = content.strip()

    if not cleaned:
        return []

    return [
        ParsedInputItem(
            raw_text=cleaned,
        )
    ]