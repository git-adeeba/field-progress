import json
import os
import re
from typing import Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ValidationError


load_dotenv()


class ExtractedFieldEvent(BaseModel):
    work_type: Optional[str] = None
    asset: Optional[str] = None
    area: Optional[str] = None
    discipline: Optional[str] = None

    progress_state: Optional[str] = None

    progress_percent: Optional[float] = None

    quantity: Optional[float] = None
    unit: Optional[str] = None

    quantity_mode: Optional[str] = None

    remarks: Optional[str] = None


# -------------------------------------------------------------------
# Gemini configuration
# -------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


def _get_gemini_client():

    if not GEMINI_API_KEY:
        return None

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


# -------------------------------------------------------------------
# General helpers
# -------------------------------------------------------------------

def _clean_text(
    text: str,
) -> str:

    return text.strip()


def _normalize_unit(
    unit: Optional[str],
) -> Optional[str]:

    if not unit:
        return None

    normalized = (
        unit
        .strip()
        .lower()
        .rstrip(".,;:")
    )

    unit_aliases = {
        "joint": "joints",
        "joints": "joints",

        "m": "m",
        "meter": "m",
        "meters": "m",
        "metre": "m",
        "metres": "m",

        "km": "km",
        "kilometer": "km",
        "kilometers": "km",
        "kilometre": "km",
        "kilometres": "km",

        "cm": "cm",
        "centimeter": "cm",
        "centimeters": "cm",
        "centimetre": "cm",
        "centimetres": "cm",

        "mm": "mm",
        "millimeter": "mm",
        "millimeters": "mm",
        "millimetre": "mm",
        "millimetres": "mm",

        "sqm": "sqm",
        "sq.m": "sqm",
        "sq.m.": "sqm",
        "m2": "sqm",
        "m²": "sqm",

        "cum": "cum",
        "cu.m": "cum",
        "cu.m.": "cum",
        "m3": "cum",
        "m³": "cum",

        "kg": "kg",
        "kgs": "kg",
        "kilogram": "kg",
        "kilograms": "kg",

        "ton": "tonnes",
        "tons": "tonnes",
        "tonne": "tonnes",
        "tonnes": "tonnes",

        "no": "nos",
        "nos": "nos",
        "number": "nos",
        "numbers": "nos",

        "unit": "units",
        "units": "units",

        "pile": "piles",
        "piles": "piles",

        "column": "columns",
        "columns": "columns",

        "beam": "beams",
        "beams": "beams",

        "panel": "panels",
        "panels": "panels",

        "support": "supports",
        "supports": "supports",

        "valve": "valves",
        "valves": "valves",

        "bolt": "bolts",
        "bolts": "bolts",

        "segment": "segments",
        "segments": "segments",

        "spool": "spools",
        "spools": "spools",
    }

    return unit_aliases.get(
        normalized,
        normalized,
    )


# -------------------------------------------------------------------
# Percentage extraction
# -------------------------------------------------------------------

def _extract_percentage(
    text: str,
) -> Optional[float]:

    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*%",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    try:
        value = float(match.group(1))

    except (
        TypeError,
        ValueError,
    ):
        return None

    if 0 <= value <= 100:
        return value

    return None


# -------------------------------------------------------------------
# Quantity mode extraction
# -------------------------------------------------------------------

def _extract_quantity_mode(
    text: str,
) -> Optional[str]:

    lower_text = text.lower()

    cumulative_patterns = [
        "total",
        "cumulative",
        "overall",
        "to date",
        "till date",
        "till now",
        "up to date",
        "so far",
        "out of",
        "as of now",
    ]

    if any(
        phrase in lower_text
        for phrase in cumulative_patterns
    ):
        return "cumulative"

    incremental_patterns = [
        "another",
        "additional",
        "extra",
        "further",
        "more",
        "today completed",
        "completed today",
        "today welded",
        "welded today",
        "today laid",
        "laid today",
        "today installed",
        "installed today",
        "today erected",
        "erected today",
        "today poured",
        "poured today",
        "during this shift",
        "this shift",
    ]

    if any(
        phrase in lower_text
        for phrase in incremental_patterns
    ):
        return "incremental"

    return None


# -------------------------------------------------------------------
# Deterministic physical quantity extraction
# -------------------------------------------------------------------

def _extract_physical_quantity(
    text: str,
) -> tuple[
    Optional[float],
    Optional[str],
]:

    # IMPORTANT:
    # Unit is deliberately a CAPTURING group.
    # Group 1 = numeric quantity
    # Group 2 = physical unit

    unit_pattern = (
        r"("
        r"joints?|"
        r"meters?|metres?|m|"
        r"kilometers?|kilometres?|km|"
        r"centimeters?|centimetres?|cm|"
        r"millimeters?|millimetres?|mm|"
        r"sqm|sq\.?\s*m\.?|m2|m²|"
        r"cum|cu\.?\s*m\.?|m3|m³|"
        r"kilograms?|kgs?|kg|"
        r"tons?|tonnes?|"
        r"nos?\.?|numbers?|"
        r"units?|"
        r"piles?|"
        r"columns?|"
        r"beams?|"
        r"panels?|"
        r"supports?|"
        r"valves?|"
        r"bolts?|"
        r"segments?|"
        r"spools?"
        r")"
    )

    pattern = (
        r"\b"
        r"(\d+(?:\.\d+)?)"
        r"\s*"
        + unit_pattern
        + r"\b"
    )

    matches = list(
        re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
    )

    if not matches:
        return (
            None,
            None,
        )

    for match in matches:

        try:
            quantity = float(
                match.group(1)
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        raw_unit = match.group(2)

        normalized_unit = (
            _normalize_unit(
                raw_unit
            )
        )

        return (
            quantity,
            normalized_unit,
        )

    return (
        None,
        None,
    )


# -------------------------------------------------------------------
# Deterministic progress-state extraction
# -------------------------------------------------------------------

def _extract_progress_state(
    text: str,
) -> Optional[str]:

    lower_text = text.lower()

    if any(
        phrase in lower_text
        for phrase in [
            "stopped",
            "blocked",
            "on hold",
            "delayed",
            "suspended",
        ]
    ):
        return "blocked"

    if any(
        word in lower_text
        for word in [
            "completed",
            "finished",
            "done",
        ]
    ):
        return "completed"

    if any(
        phrase in lower_text
        for phrase in [
            "in progress",
            "ongoing",
            "under progress",
        ]
    ):
        return "in_progress"

    if any(
        word in lower_text
        for word in [
            "started",
            "commenced",
            "began",
        ]
    ):
        return "started"

    # Physical work verbs mean work is occurring.
    # They do NOT mean the whole schedule activity
    # has been completed.
    if any(
        word in lower_text
        for word in [
            "welded",
            "laid",
            "installed",
            "erected",
            "poured",
            "fabricated",
            "excavated",
            "painted",
            "tested",
            "backfilled",
        ]
    ):
        return "in_progress"

    return None


# -------------------------------------------------------------------
# Deterministic work-type extraction
# -------------------------------------------------------------------

def _extract_work_type(
    text: str,
) -> Optional[str]:

    lower_text = text.lower()

    mappings = [
        (
            [
                "excavation",
                "excavated",
                "digging",
                "dug",
            ],
            "excavation",
        ),
        (
            [
                "concreting",
                "concrete",
                "pouring",
                "poured",
            ],
            "concreting",
        ),
        (
            [
                "welding",
                "welded",
                "weld",
            ],
            "welding",
        ),
        (
            [
                "fabrication",
                "fabricated",
                "fabricating",
            ],
            "fabrication",
        ),
        (
            [
                "installation",
                "installed",
                "installing",
            ],
            "installation",
        ),
        (
            [
                "erection",
                "erected",
                "erecting",
            ],
            "erection",
        ),
        (
            [
                "backfilling",
                "backfilled",
                "backfill",
            ],
            "backfilling",
        ),
        (
            [
                "painting",
                "painted",
                "paint",
            ],
            "painting",
        ),
        (
            [
                "testing",
                "tested",
                "test",
            ],
            "testing",
        ),
        (
            [
                "commissioning",
                "commissioned",
            ],
            "commissioning",
        ),
        (
            [
                "piping",
                "pipe laying",
                "pipeline laying",
            ],
            "piping",
        ),
    ]

    for (
        keywords,
        normalized_value,
    ) in mappings:

        if any(
            keyword in lower_text
            for keyword in keywords
        ):
            return normalized_value

    return None


# -------------------------------------------------------------------
# Deterministic area extraction
# -------------------------------------------------------------------

def _extract_area(
    text: str,
) -> Optional[str]:

    rack_match = re.search(
        r"\brack\s+row\s+"
        r"([a-z0-9][a-z0-9\-]*)",
        text,
        flags=re.IGNORECASE,
    )

    if rack_match:

        return (
            f"Rack Row "
            f"{rack_match.group(1)}"
        )

    area_match = re.search(
        r"\barea\s+"
        r"([a-z0-9][a-z0-9\-]*)",
        text,
        flags=re.IGNORECASE,
    )

    if area_match:

        return (
            f"Area "
            f"{area_match.group(1)}"
        )

    return None


# -------------------------------------------------------------------
# Deterministic asset extraction
# -------------------------------------------------------------------

def _extract_asset(
    text: str,
) -> Optional[str]:

    patterns = [
        (
            r"\bline\s+"
            r"([a-z0-9\-]+)",
            lambda match:
                f"Line {match.group(1)}",
        ),
        (
            r"\bpump\s+house\b",
            lambda match:
                "Pump House",
        ),
        (
            r"\btank\s+foundation\b",
            lambda match:
                "Tank Foundation",
        ),
        (
            r"\bpipe\s+rack\b",
            lambda match:
                "Pipe Rack",
        ),
        (
            r"\bcontrol\s+room\b",
            lambda match:
                "Control Room",
        ),
        (
            r"\bsubstation\b",
            lambda match:
                "Substation",
        ),
        (
            r"\bcompressor\b",
            lambda match:
                "Compressor",
        ),
        (
            r"\breactor\b",
            lambda match:
                "Reactor",
        ),
        (
            r"\bpipeline\b",
            lambda match:
                "Pipeline",
        ),
        (
            r"\btank\b",
            lambda match:
                "Tank",
        ),
        (
            r"\bpump\b",
            lambda match:
                "Pump",
        ),
    ]

    for (
        pattern,
        formatter,
    ) in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return formatter(match)

    return None


# -------------------------------------------------------------------
# Deterministic evidence extraction
# -------------------------------------------------------------------

def _extract_deterministic_evidence(
    raw_text: str,
    discipline: Optional[str] = None,
    area: Optional[str] = None,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
) -> ExtractedFieldEvent:

    text = _clean_text(raw_text)

    detected_quantity = None
    detected_unit = None

    if quantity is not None:

        detected_quantity = float(
            quantity
        )

        detected_unit = (
            _normalize_unit(
                unit
            )
        )

    else:

        (
            detected_quantity,
            detected_unit,
        ) = _extract_physical_quantity(
            text
        )

        if (
            detected_unit is None
            and unit
        ):
            detected_unit = (
                _normalize_unit(
                    unit
                )
            )

    detected_area = (
        area
        or _extract_area(
            text
        )
    )

    return ExtractedFieldEvent(
        work_type=(
            _extract_work_type(
                text
            )
        ),
        asset=(
            _extract_asset(
                text
            )
        ),
        area=detected_area,
        discipline=discipline,
        progress_state=(
            _extract_progress_state(
                text
            )
        ),
        progress_percent=(
            _extract_percentage(
                text
            )
        ),
        quantity=detected_quantity,
        unit=detected_unit,
        quantity_mode=(
            _extract_quantity_mode(
                text
            )
        ),
        remarks=text,
    )


# -------------------------------------------------------------------
# Deterministic fallback
# -------------------------------------------------------------------

def extract_field_event_fallback(
    raw_text: str,
    discipline: Optional[str] = None,
    area: Optional[str] = None,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
) -> ExtractedFieldEvent:

    return (
        _extract_deterministic_evidence(
            raw_text=raw_text,
            discipline=discipline,
            area=area,
            quantity=quantity,
            unit=unit,
        )
    )


# -------------------------------------------------------------------
# Gemini extraction
# -------------------------------------------------------------------

def extract_field_event_with_gemini(
    raw_text: str,
    discipline: Optional[str] = None,
    area: Optional[str] = None,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
) -> ExtractedFieldEvent:

    client = _get_gemini_client()

    if client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    prompt = f"""
You are an information extraction component for an
infrastructure project progress tracking system.

Convert the messy field update into one structured
field execution event.

FIELD UPDATE:
{raw_text}

KNOWN STRUCTURED CONTEXT:
discipline: {discipline}
area: {area}
quantity: {quantity}
unit: {unit}

Extract:

- work_type
- asset
- area
- discipline
- progress_state
- progress_percent
- quantity
- unit
- quantity_mode
- remarks

Rules:

1. Normalize construction terminology.

Examples:
"digging" -> "excavation"
"pouring concrete" -> "concreting"

2. progress_state must be one of:
"started"
"in_progress"
"completed"
"blocked"
null

3. progress_percent is ONLY for an explicitly stated
percentage.

Example:
"45% complete"
-> progress_percent = 45

Do NOT estimate a percentage.

4. quantity must contain an explicitly reported
physical quantity when one is present.

Example:
"another 10 joints welded"
-> quantity = 10
-> unit = "joints"

5. quantity_mode must be:

"incremental"
when the field update clearly reports NEW work done
in this update.

Examples:
"another 20 joints welded"
"additional 15 metres laid"

"cumulative"
when the update clearly reports TOTAL progress to date.

Examples:
"total 40 joints complete"
"40 out of 100 joints completed"
"cumulative 75 metres laid"

null
when it is unclear whether the quantity is incremental
or cumulative.

DO NOT GUESS quantity_mode.

6. Preserve structured context supplied above unless
the update clearly gives more specific information.

7. Never invent quantities, percentages, locations,
assets or disciplines.

8. remarks must preserve the original field update.

Return ONLY valid JSON.

Required JSON shape:

{{
  "work_type": null,
  "asset": null,
  "area": null,
  "discipline": null,
  "progress_state": null,
  "progress_percent": null,
  "quantity": null,
  "unit": null,
  "quantity_mode": null,
  "remarks": "{raw_text}"
}}
"""

    response = (
        client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type":
                    "application/json",
            },
        )
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty extraction response."
        )

    try:

        raw_result = json.loads(
            response.text
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Gemini returned invalid JSON."
        ) from exc

    if (
        not raw_result.get(
            "discipline"
        )
        and discipline
    ):
        raw_result[
            "discipline"
        ] = discipline

    if (
        not raw_result.get("area")
        and area
    ):
        raw_result[
            "area"
        ] = area

    if (
        raw_result.get(
            "quantity"
        )
        is None
        and quantity is not None
    ):
        raw_result[
            "quantity"
        ] = quantity

    if (
        not raw_result.get("unit")
        and unit
    ):
        raw_result[
            "unit"
        ] = _normalize_unit(
            unit
        )

    raw_result[
        "remarks"
    ] = raw_text.strip()

    try:

        return (
            ExtractedFieldEvent
            .model_validate(
                raw_result
            )
        )

    except ValidationError as exc:

        raise RuntimeError(
            "Gemini extraction failed schema validation."
        ) from exc


# -------------------------------------------------------------------
# Gemini + deterministic evidence merge
# -------------------------------------------------------------------

def _merge_extractions(
    raw_text: str,
    ai_result: ExtractedFieldEvent,
    deterministic_result: ExtractedFieldEvent,
) -> ExtractedFieldEvent:

    # Explicit physical evidence from raw text gets priority.
    # Gemini handles semantic interpretation/context.

    progress_percent = (
        deterministic_result.progress_percent
        if deterministic_result.progress_percent
        is not None
        else ai_result.progress_percent
    )

    quantity = (
        deterministic_result.quantity
        if deterministic_result.quantity
        is not None
        else ai_result.quantity
    )

    unit = (
        deterministic_result.unit
        or _normalize_unit(
            ai_result.unit
        )
    )

    quantity_mode = (
        deterministic_result.quantity_mode
        or ai_result.quantity_mode
    )

    work_type = (
        ai_result.work_type
        or deterministic_result.work_type
    )

    asset = (
        ai_result.asset
        or deterministic_result.asset
    )

    area = (
        ai_result.area
        or deterministic_result.area
    )

    discipline = (
        ai_result.discipline
        or deterministic_result.discipline
    )

    progress_state = (
        ai_result.progress_state
        or deterministic_result.progress_state
    )

    return ExtractedFieldEvent(
        work_type=work_type,
        asset=asset,
        area=area,
        discipline=discipline,
        progress_state=progress_state,
        progress_percent=progress_percent,
        quantity=quantity,
        unit=unit,
        quantity_mode=quantity_mode,
        remarks=raw_text.strip(),
    )


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

def _validate_final_extraction(
    extracted: ExtractedFieldEvent,
) -> ExtractedFieldEvent:

    progress_percent = (
        extracted.progress_percent
    )

    if progress_percent is not None:

        try:
            progress_percent = float(
                progress_percent
            )

        except (
            TypeError,
            ValueError,
        ):
            progress_percent = None

        if (
            progress_percent is not None
            and not (
                0
                <= progress_percent
                <= 100
            )
        ):
            progress_percent = None

    quantity = extracted.quantity

    if quantity is not None:

        try:
            quantity = float(quantity)

        except (
            TypeError,
            ValueError,
        ):
            quantity = None

        if (
            quantity is not None
            and quantity < 0
        ):
            quantity = None

    quantity_mode = (
        extracted.quantity_mode
    )

    if quantity_mode not in [
        "incremental",
        "cumulative",
        None,
    ]:
        quantity_mode = None

    progress_state = (
        extracted.progress_state
    )

    if progress_state not in [
        "started",
        "in_progress",
        "completed",
        "blocked",
        None,
    ]:
        progress_state = None

    return ExtractedFieldEvent(
        work_type=extracted.work_type,
        asset=extracted.asset,
        area=extracted.area,
        discipline=extracted.discipline,
        progress_state=progress_state,
        progress_percent=progress_percent,
        quantity=quantity,
        unit=_normalize_unit(
            extracted.unit
        ),
        quantity_mode=quantity_mode,
        remarks=extracted.remarks,
    )


# -------------------------------------------------------------------
# Public entry point
# -------------------------------------------------------------------

def extract_field_event(
    raw_text: str,
    discipline: Optional[str] = None,
    area: Optional[str] = None,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
) -> ExtractedFieldEvent:

    try:

        deterministic_result = (
            _extract_deterministic_evidence(
                raw_text=raw_text,
                discipline=discipline,
                area=area,
                quantity=quantity,
                unit=unit,
            )
        )

        print(
            "[AI EXTRACTION] "
            f"Deterministic evidence: "
            f"{deterministic_result.model_dump()}"
        )

    except Exception as exc:

        # Deterministic recovery should never bring down
        # the whole matching API.
        print(
            "[AI EXTRACTION] "
            f"Deterministic extraction failed: {exc}"
        )

        deterministic_result = (
            ExtractedFieldEvent(
                discipline=discipline,
                area=area,
                quantity=quantity,
                unit=_normalize_unit(
                    unit
                ),
                remarks=raw_text.strip(),
            )
        )

    try:

        ai_result = (
            extract_field_event_with_gemini(
                raw_text=raw_text,
                discipline=discipline,
                area=area,
                quantity=quantity,
                unit=unit,
            )
        )

        final_result = (
            _merge_extractions(
                raw_text=raw_text,
                ai_result=ai_result,
                deterministic_result=(
                    deterministic_result
                ),
            )
        )

        final_result = (
            _validate_final_extraction(
                final_result
            )
        )

        print(
            "[AI EXTRACTION] "
            "Gemini + deterministic evidence merged."
        )

        print(
            "[AI EXTRACTION] "
            f"Final extraction: "
            f"{final_result.model_dump()}"
        )

        return final_result

    except Exception as exc:

        print(
            "[AI EXTRACTION] "
            f"Gemini unavailable/failed: {exc}"
        )

        print(
            "[AI EXTRACTION] "
            "Using deterministic extraction."
        )

        final_result = (
            _validate_final_extraction(
                deterministic_result
            )
        )

        print(
            "[AI EXTRACTION] "
            f"Final extraction: "
            f"{final_result.model_dump()}"
        )

        return final_result