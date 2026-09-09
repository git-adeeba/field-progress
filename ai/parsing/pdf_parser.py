from io import BytesIO
import re

from pypdf import PdfReader

from ai.parsing.models import ParsedInputItem


DISCIPLINES = {
    "civil",
    "mechanical",
    "electrical",
    "instrumentation",
    "piping",
}

HEADER_LINES = {
    "daily site progress report",
    "daily progress report",
    "daily progress report - test file",
    "field execution updates",
    "field update",
    "id",
    "discipline",
    "discipline / area",
    "area",
    "progress",
    "status",
    "remarks",
    "update",
    "description",
}

UPDATE_ID_PATTERN = re.compile(r"^FU-\d+$", re.IGNORECASE)

DISCIPLINE_AREA_PATTERN = re.compile(
    r"^(civil|mechanical|electrical|instrumentation|piping)\s*/\s*(.+)$",
    re.IGNORECASE,
)

AREA_PATTERN = re.compile(
    r"^area\s+[a-z0-9_-]+$",
    re.IGNORECASE,
)

SUPERVISOR_NOTE_PATTERN = re.compile(
    r"^supervisor\s+note\s*:",
    re.IGNORECASE,
)


def clean_line(value: str) -> str:
    return " ".join(value.strip().split())


def is_ignore_line(line: str) -> bool:
    lowered = line.lower().strip()

    if lowered in HEADER_LINES:
        return True

    if lowered.startswith("project:"):
        return True

    if lowered.startswith("[page"):
        return True

    if "intended to test parsing" in lowered:
        return True

    return False


def _extract_lines(file_bytes: bytes) -> list[str]:
    reader = PdfReader(BytesIO(file_bytes))
    lines: list[str] = []

    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue

        for raw_line in text.splitlines():
            line = clean_line(raw_line)

            if not line:
                continue

            if is_ignore_line(line):
                continue

            lines.append(line)

    return lines


def _looks_like_metadata(line: str) -> bool:
    lowered = line.lower()

    if UPDATE_ID_PATTERN.match(line):
        return True

    if lowered in DISCIPLINES:
        return True

    if DISCIPLINE_AREA_PATTERN.match(line):
        return True

    if AREA_PATTERN.match(line):
        return True

    return False


def _build_item(block: list[str]) -> ParsedInputItem | None:
    if not block:
        return None

    discipline = None
    area = None
    content: list[str] = []

    for line in block:
        if UPDATE_ID_PATTERN.match(line):
            continue

        discipline_area = DISCIPLINE_AREA_PATTERN.match(line)
        if discipline_area:
            discipline = discipline_area.group(1).title()
            area = clean_line(discipline_area.group(2))
            continue

        lowered = line.lower()

        if lowered in DISCIPLINES and discipline is None:
            discipline = line.title()
            continue

        if AREA_PATTERN.match(line) and area is None:
            area = line
            continue

        content.append(line)

    raw_text = clean_line(" ".join(content))

    if not raw_text:
        return None

    return ParsedInputItem(
        raw_text=raw_text,
        discipline=discipline,
        area=area,
    )


def _parse_fu_blocks(lines: list[str]) -> list[ParsedInputItem]:
    """
    Structured site-report mode.

    Each FU-### marker starts one logical field update. Everything until the
    next FU marker belongs to the same update.

    A trailing document-level "Supervisor Note:" is NOT part of the final
    field update. Once encountered, structured FU parsing stops there so the
    final update cannot inherit unrelated status/remarks from that note.
    """
    marker_indexes = [
        index
        for index, line in enumerate(lines)
        if UPDATE_ID_PATTERN.match(line)
    ]

    if not marker_indexes:
        return []

    supervisor_note_index = next(
        (
            index
            for index, line in enumerate(lines)
            if SUPERVISOR_NOTE_PATTERN.match(line)
        ),
        None,
    )

    items: list[ParsedInputItem] = []

    for position, start in enumerate(marker_indexes):
        next_marker = (
            marker_indexes[position + 1]
            if position + 1 < len(marker_indexes)
            else len(lines)
        )

        end = next_marker

        if (
            supervisor_note_index is not None
            and supervisor_note_index > start
            and supervisor_note_index < end
        ):
            end = supervisor_note_index

        block = lines[start:end]
        item = _build_item(block)

        if item is not None:
            items.append(item)

        if (
            supervisor_note_index is not None
            and end == supervisor_note_index
        ):
            break

    return items


def _parse_fallback(lines: list[str]) -> list[ParsedInputItem]:
    """
    Fallback for ordinary PDFs without FU-### row identifiers.

    Consecutive text is grouped into paragraph-like chunks instead of creating
    one ParsedInputItem for every extracted PDF line.

    A document-level "Supervisor Note:" terminates field-update parsing rather
    than being merged into the preceding update.
    """
    items: list[ParsedInputItem] = []
    current: list[str] = []
    discipline = None
    area = None

    def flush() -> None:
        nonlocal current, discipline, area

        raw_text = clean_line(" ".join(current))

        if raw_text:
            items.append(
                ParsedInputItem(
                    raw_text=raw_text,
                    discipline=discipline,
                    area=area,
                )
            )

        current = []
        discipline = None
        area = None

    for line in lines:
        if SUPERVISOR_NOTE_PATTERN.match(line):
            flush()
            break

        lowered = line.lower()

        discipline_area = DISCIPLINE_AREA_PATTERN.match(line)
        if discipline_area:
            if current:
                flush()

            discipline = discipline_area.group(1).title()
            area = clean_line(discipline_area.group(2))
            continue

        if lowered in DISCIPLINES:
            if current:
                flush()

            discipline = line.title()
            continue

        if AREA_PATTERN.match(line):
            area = line
            continue

        current.append(line)

        # Keep chunks reasonably sized for extraction.
        if len(" ".join(current)) >= 700:
            flush()

    flush()
    return items


def parse_pdf(file_bytes: bytes) -> list[ParsedInputItem]:
    lines = _extract_lines(file_bytes)

    if not lines:
        return []

    structured_items = _parse_fu_blocks(lines)

    if structured_items:
        return structured_items

    return _parse_fallback(lines)
