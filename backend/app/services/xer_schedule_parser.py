from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(
        str(value)
        .replace("\x00", "")
        .strip()
        .split()
    )


def parse_float(value: Any) -> float | None:
    text = clean_text(value)

    if not text:
        return None

    try:
        return float(
            text.replace(",", "")
        )
    except ValueError:
        return None


DATE_FORMATS = [
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d-%b-%y",
    "%d-%b-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
]


def parse_date(value: Any) -> str | None:
    text = clean_text(value)

    if not text:
        return None

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )
            return parsed.isoformat()
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.isoformat()

    except ValueError:
        return None


def parse_xer_tables(
    file_bytes: bytes,
) -> dict[str, list[dict[str, str]]]:
    text = file_bytes.decode(
        "utf-8-sig",
        errors="replace",
    )

    tables: dict[
        str,
        list[dict[str, str]]
    ] = {}

    current_table: str | None = None
    fields: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r\n")

        if not line:
            continue

        parts = line.split("\t")

        marker = (
            parts[0].strip()
            if parts
            else ""
        )

        if marker == "%T":
            current_table = (
                parts[1].strip()
                if len(parts) > 1
                else None
            )

            fields = []

            if current_table:
                tables.setdefault(
                    current_table,
                    [],
                )

            continue

        if marker == "%F":
            fields = [
                clean_text(value)
                for value in parts[1:]
            ]
            continue

        if marker == "%R":
            if (
                not current_table
                or not fields
            ):
                continue

            values = parts[1:]

            row = {}

            for index, field in enumerate(
                fields
            ):
                value = (
                    values[index]
                    if index < len(values)
                    else ""
                )

                row[field] = value

            tables[current_table].append(
                row
            )

    return tables


def build_wbs_lookup(
    tables: dict[
        str,
        list[dict[str, str]]
    ],
) -> dict[str, str]:
    rows = tables.get(
        "PROJWBS",
        [],
    )

    by_id = {
        clean_text(
            row.get("wbs_id")
        ): row
        for row in rows
        if clean_text(
            row.get("wbs_id")
        )
    }

    cache: dict[str, str] = {}

    def resolve_wbs(
        wbs_id: str,
    ) -> str:
        if not wbs_id:
            return ""

        if wbs_id in cache:
            return cache[wbs_id]

        row = by_id.get(
            wbs_id
        )

        if not row:
            return ""

        short_name = (
            clean_text(
                row.get(
                    "wbs_short_name"
                )
            )
            or clean_text(
                row.get(
                    "wbs_name"
                )
            )
        )

        parent_id = clean_text(
            row.get(
                "parent_wbs_id"
            )
        )

        parent_path = ""

        if (
            parent_id
            and parent_id != wbs_id
        ):
            parent_path = resolve_wbs(
                parent_id
            )

        if (
            parent_path
            and short_name
        ):
            result = (
                f"{parent_path}.{short_name}"
            )
        else:
            result = (
                short_name
                or parent_path
            )

        cache[wbs_id] = result
        return result

    return {
        wbs_id: resolve_wbs(
            wbs_id
        )
        for wbs_id in by_id
    }


def convert_status(
    value: Any,
) -> str:
    status = clean_text(
        value
    ).upper()

    if status in {
        "TK_COMPLETE",
        "COMPLETE",
        "COMPLETED",
    }:
        return "completed"

    if status in {
        "TK_ACTIVE",
        "ACTIVE",
        "IN_PROGRESS",
    }:
        return "in_progress"

    return "not_started"


def extract_actual_progress(
    row: dict[str, str],
) -> float:
    """
    Primavera completion fields describe actual/physical completion,
    not planned progress.

    Different P6 exports can expose different names, so try the common
    physical/complete percentage columns in order.
    """
    candidates = [
        row.get("phys_complete_pct"),
        row.get("complete_pct"),
        row.get("pct_complete"),
    ]

    for value in candidates:
        parsed = parse_float(
            value
        )

        if parsed is None:
            continue

        # Some exports may use 0..1 instead of 0..100.
        if 0 <= parsed <= 1:
            parsed *= 100

        return max(
            0.0,
            min(
                100.0,
                parsed,
            ),
        )

    return 0.0


def convert_dependency_type(
    value: Any,
) -> str:
    dependency = (
        clean_text(value)
        .upper()
        .replace(
            "PR_",
            "",
        )
    )

    if dependency in {
        "FS",
        "SS",
        "FF",
        "SF",
    }:
        return dependency

    return "FS"


def convert_lag_hours_to_days(
    value: Any,
) -> int:
    lag_hours = parse_float(
        value
    )

    if lag_hours is None:
        return 0

    return int(
        round(
            lag_hours / 8
        )
    )


def parse_xer_schedule(
    file_bytes: bytes,
) -> dict:
    tables = parse_xer_tables(
        file_bytes
    )

    task_rows = tables.get(
        "TASK",
        [],
    )

    if not task_rows:
        raise ValueError(
            "No TASK table was found in the XER file."
        )

    wbs_lookup = build_wbs_lookup(
        tables
    )

    activity_code_by_task_id: dict[
        str,
        str
    ] = {}

    activities = []
    warnings = []
    errors = []

    for index, row in enumerate(
        task_rows,
        start=1,
    ):
        task_id = clean_text(
            row.get(
                "task_id"
            )
        )

        activity_code = clean_text(
            row.get(
                "task_code"
            )
        )

        activity_name = clean_text(
            row.get(
                "task_name"
            )
        )

        if not activity_code:
            errors.append({
                "row": index,
                "field": "task_code",
                "message":
                    "Primavera task is missing its activity code.",
            })
            continue

        if not activity_name:
            errors.append({
                "row": index,
                "field": "task_name",
                "message":
                    f"Activity {activity_code} has no activity name.",
            })
            continue

        if task_id:
            activity_code_by_task_id[
                task_id
            ] = activity_code

        wbs_id = clean_text(
            row.get(
                "wbs_id"
            )
        )

        planned_start = (
            parse_date(
                row.get(
                    "target_start_date"
                )
            )
            or parse_date(
                row.get(
                    "early_start_date"
                )
            )
            or parse_date(
                row.get(
                    "start_date"
                )
            )
        )

        planned_finish = (
            parse_date(
                row.get(
                    "target_end_date"
                )
            )
            or parse_date(
                row.get(
                    "early_end_date"
                )
            )
            or parse_date(
                row.get(
                    "end_date"
                )
            )
        )

        planned_quantity = (
            parse_float(
                row.get(
                    "target_work_qty"
                )
            )
            or parse_float(
                row.get(
                    "target_equip_qty"
                )
            )
        )

        actual_progress = (
            extract_actual_progress(
                row
            )
        )

        status = convert_status(
            row.get(
                "status_code"
            )
        )

        # Keep status/progress internally consistent even when the
        # export omits or disagrees on one of them.
        if status == "completed":
            actual_progress = 100.0
        elif (
            status == "not_started"
            and actual_progress > 0
        ):
            status = "in_progress"

        activities.append({
            "activity_code":
                activity_code,

            "activity_name":
                activity_name,

            "wbs_level":
                wbs_lookup.get(
                    wbs_id
                )
                or None,

            "discipline":
                None,

            "area":
                None,

            "planned_start":
                planned_start,

            "planned_finish":
                planned_finish,

            # XER physical completion is NOT planned progress.
            # Planned progress remains zero unless calculated later
            # by the project's planning/progress engine.
            "planned_progress":
                0.0,

            "actual_progress":
                actual_progress,

            "planned_quantity":
                planned_quantity,

            "quantity_unit":
                None,

            "status":
                status,

            "source_row":
                index,
        })

    dependencies = []

    relationship_rows = tables.get(
        "TASKPRED",
        [],
    )

    for index, row in enumerate(
        relationship_rows,
        start=1,
    ):
        successor_task_id = clean_text(
            row.get(
                "task_id"
            )
        )

        predecessor_task_id = clean_text(
            row.get(
                "pred_task_id"
            )
        )

        successor_code = (
            activity_code_by_task_id.get(
                successor_task_id
            )
        )

        predecessor_code = (
            activity_code_by_task_id.get(
                predecessor_task_id
            )
        )

        if (
            not successor_code
            or not predecessor_code
        ):
            warnings.append({
                "row": index,
                "field": "TASKPRED",
                "message":
                    "A Primavera relationship could not be linked to both activities.",
            })
            continue

        dependencies.append({
            "successor_code":
                successor_code,

            "predecessor_code":
                predecessor_code,

            "dependency_type":
                convert_dependency_type(
                    row.get(
                        "pred_type"
                    )
                ),

            "lag_days":
                convert_lag_hours_to_days(
                    row.get(
                        "lag_hr_cnt"
                    )
                ),

            "source_row":
                index,
        })

    return {
        "activities": activities,
        "dependencies": dependencies,
        "errors": errors,
        "warnings": warnings,
        "source_rows":
            len(task_rows),
    }
