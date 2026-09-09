from io import BytesIO
import re

from pypdf import PdfReader

from ai.parsing.models import ParsedInputItem


IGNORE_LINES = {
    "daily progress report - test file",
    "field execution updates",
    "field update",
    "discipline",
    "area",
}


DISCIPLINES = {
    "civil",
    "mechanical",
    "electrical",
    "instrumentation",
    "piping",
}


AREA_PATTERN = re.compile(
    r"^area\s+[a-z0-9\-]+$",
    re.IGNORECASE,
)


def clean_line(
    value: str,
) -> str:
    return " ".join(
        value.strip().split()
    )


def is_ignore_line(
    line: str,
) -> bool:
    lowered = line.lower()

    if lowered in IGNORE_LINES:
        return True

    if lowered.startswith("project:"):
        return True

    if lowered.startswith("[page"):
        return True

    if (
        "intended to test parsing"
        in lowered
    ):
        return True

    return False


def parse_pdf(
    file_bytes: bytes,
) -> list[ParsedInputItem]:

    reader = PdfReader(
        BytesIO(file_bytes)
    )

    lines: list[str] = []

    for page in reader.pages:
        text = page.extract_text()

        if not text:
            continue

        for raw_line in text.splitlines():

            line = clean_line(
                raw_line
            )

            if not line:
                continue

            if is_ignore_line(
                line
            ):
                continue

            lines.append(
                line
            )

    items: list[ParsedInputItem] = []

    index = 0

    while index < len(lines):

        current = lines[index]

        current_lower = (
            current.lower()
        )

        if (
            current_lower
            in DISCIPLINES
        ):
            index += 1
            continue

        if AREA_PATTERN.match(
            current
        ):
            index += 1
            continue

        raw_text = current

        discipline = None
        area = None

        if (
            index + 1 < len(lines)
            and lines[index + 1].lower()
            in DISCIPLINES
        ):
            discipline = (
                lines[index + 1]
            )

            index += 1

        if (
            index + 1 < len(lines)
            and AREA_PATTERN.match(
                lines[index + 1]
            )
        ):
            area = (
                lines[index + 1]
            )

            index += 1

        items.append(
            ParsedInputItem(
                raw_text=raw_text,
                discipline=discipline,
                area=area,
            )
        )

        index += 1

    return items