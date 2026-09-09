import csv
import io
from typing import Any

from ai.parsing.models import ParsedInputItem


TEXT_COLUMNS = [
    "raw_text",
    "update",
    "field_update",
    "progress_update",
    "remarks",
    "description",
    "work_description",
    "activity",
]


def clean_value(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def find_value(
    row: dict,
    possible_columns: list[str],
):
    normalized = {
        str(key).strip().lower(): value
        for key, value in row.items()
    }

    for column in possible_columns:
        if column in normalized:
            value = clean_value(normalized[column])

            if value:
                return value

    return None


def build_row_text(row: dict) -> str:
    direct_text = find_value(
        row,
        TEXT_COLUMNS,
    )

    if direct_text:
        return direct_text

    parts = []

    for key, value in row.items():
        cleaned = clean_value(value)

        if cleaned:
            parts.append(
                f"{key}: {cleaned}"
            )

    return " | ".join(parts)


def parse_csv(
    file_bytes: bytes,
) -> list[ParsedInputItem]:

    text = file_bytes.decode(
        "utf-8-sig",
        errors="replace",
    )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    items: list[ParsedInputItem] = []

    for index, row in enumerate(
        reader,
        start=2,
    ):
        raw_text = build_row_text(row)

        if not raw_text:
            continue

        discipline = find_value(
            row,
            ["discipline"],
        )

        area = find_value(
            row,
            ["area", "location"],
        )

        unit = find_value(
            row,
            ["unit", "uom"],
        )

        quantity_raw = find_value(
            row,
            [
                "quantity",
                "qty",
                "actual_quantity",
            ],
        )

        quantity = None

        if quantity_raw is not None:
            try:
                quantity = float(
                    quantity_raw
                )
            except ValueError:
                quantity = None

        items.append(
            ParsedInputItem(
                raw_text=raw_text,
                discipline=discipline,
                area=area,
                quantity=quantity,
                unit=unit,
                source_row=index,
            )
        )

    return items