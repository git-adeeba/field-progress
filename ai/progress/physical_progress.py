from typing import Any


def normalize_unit(
    value,
) -> str:

    if value is None:
        return ""

    unit = (
        str(value)
        .strip()
        .lower()
    )

    aliases = {
        "meter": "m",
        "meters": "m",
        "metre": "m",
        "metres": "m",

        "kilometer": "km",
        "kilometers": "km",
        "kilometre": "km",
        "kilometres": "km",

        "joint": "joints",
        "joints": "joints",

        "item": "items",
        "items": "items",

        "nos": "nos",
        "no": "nos",
        "number": "nos",

        "m3": "m3",
        "m³": "m3",
        "cum": "m3",
    }

    return aliases.get(
        unit,
        unit,
    )


def clamp_progress(
    value: float,
) -> float:

    return round(
        max(
            0.0,
            min(
                100.0,
                float(value),
            ),
        ),
        2,
    )


def calculate_physical_progress(
    activity: dict[str, Any],
    extracted,
) -> dict:

    current_progress = float(
        activity.get(
            "actual_progress"
        )
        or 0
    )

    current_quantity = float(
        activity.get(
            "actual_quantity"
        )
        or 0
    )

    planned_quantity_raw = (
        activity.get(
            "planned_quantity"
        )
    )

    planned_quantity = None

    if planned_quantity_raw is not None:
        planned_quantity = float(
            planned_quantity_raw
        )

    activity_unit = (
        normalize_unit(
            activity.get(
                "quantity_unit"
            )
        )
    )

    event_unit = (
        normalize_unit(
            getattr(
                extracted,
                "unit",
                None,
            )
        )
    )

    progress_percent = getattr(
        extracted,
        "progress_percent",
        None,
    )

    quantity = getattr(
        extracted,
        "quantity",
        None,
    )

    quantity_mode = getattr(
        extracted,
        "quantity_mode",
        None,
    )

    progress_state = getattr(
        extracted,
        "progress_state",
        None,
    )

    result = {
        "method":
            "no_measurable_progress",

        "should_update_progress":
            False,

        "should_update_quantity":
            False,

        "previous_progress":
            round(
                current_progress,
                2,
            ),

        "new_progress":
            round(
                current_progress,
                2,
            ),

        "progress_contribution":
            0.0,

        "previous_quantity":
            round(
                current_quantity,
                2,
            ),

        "new_quantity":
            round(
                current_quantity,
                2,
            ),

        "reason":
            (
                "No measurable progress "
                "evidence was provided."
            ),
    }

    # ---------------------------------------------------------------
    # 1. Explicit completion
    # ---------------------------------------------------------------

    if (
        progress_state
        and progress_state.lower()
        == "completed"
        and progress_percent is None
        and quantity is None
    ):

        target_progress = 100.0

        result[
            "method"
        ] = "completion_state"

        result[
            "should_update_progress"
        ] = True

        result[
            "new_progress"
        ] = target_progress

        result[
            "progress_contribution"
        ] = round(
            max(
                0,
                target_progress
                - current_progress,
            ),
            2,
        )

        result[
            "reason"
        ] = (
            "Activity explicitly "
            "reported as completed."
        )

        return result

    # ---------------------------------------------------------------
    # 2. Direct percentage
    # ---------------------------------------------------------------

    if progress_percent is not None:

        target_progress = (
            clamp_progress(
                progress_percent
            )
        )

        # Do not automatically move progress backwards.
        if (
            target_progress
            < current_progress
        ):

            result[
                "method"
            ] = (
                "direct_percentage_"
                "lower_than_current"
            )

            result[
                "reason"
            ] = (
                "Reported percentage is "
                "lower than current verified "
                "progress. Existing progress "
                "was preserved."
            )

            return result

        result[
            "method"
        ] = "direct_percentage"

        result[
            "should_update_progress"
        ] = True

        result[
            "new_progress"
        ] = target_progress

        result[
            "progress_contribution"
        ] = round(
            target_progress
            - current_progress,
            2,
        )

        result[
            "reason"
        ] = (
            "Progress updated from "
            "explicit percentage."
        )

        return result

    # ---------------------------------------------------------------
    # 3. Quantity-based progress
    # ---------------------------------------------------------------

    if quantity is not None:

        quantity = float(
            quantity
        )

        if quantity < 0:
            result[
                "method"
            ] = "invalid_quantity"

            result[
                "reason"
            ] = (
                "Negative quantity "
                "was ignored."
            )

            return result

        if (
            planned_quantity is None
            or planned_quantity <= 0
        ):
            result[
                "method"
            ] = (
                "quantity_without_"
                "baseline"
            )

            result[
                "reason"
            ] = (
                "Quantity was reported "
                "but the activity has no "
                "planned quantity baseline."
            )

            return result

        if (
            activity_unit
            and event_unit
            and activity_unit
            != event_unit
        ):
            result[
                "method"
            ] = "unit_mismatch"

            result[
                "reason"
            ] = (
                f"Reported unit '{event_unit}' "
                f"does not match activity unit "
                f"'{activity_unit}'."
            )

            return result

        # Ambiguous quantity:
        # don't guess incremental vs cumulative.
        if quantity_mode not in [
            "incremental",
            "cumulative",
        ]:

            result[
                "method"
            ] = (
                "ambiguous_quantity"
            )

            result[
                "reason"
            ] = (
                "Quantity was reported, "
                "but it is unclear whether "
                "it is incremental or "
                "cumulative. Progress was "
                "not changed."
            )

            return result

        if (
            quantity_mode
            == "incremental"
        ):

            new_quantity = (
                current_quantity
                + quantity
            )

        else:
            new_quantity = quantity

            # Don't silently reduce already
            # verified physical quantity.
            if (
                new_quantity
                < current_quantity
            ):
                result[
                    "method"
                ] = (
                    "cumulative_quantity_"
                    "lower_than_current"
                )

                result[
                    "reason"
                ] = (
                    "Reported cumulative "
                    "quantity is lower than "
                    "current verified quantity. "
                    "Existing progress was "
                    "preserved."
                )

                return result

        calculated_progress = (
            new_quantity
            / planned_quantity
            * 100
        )

        target_progress = (
            clamp_progress(
                calculated_progress
            )
        )

        result[
            "method"
        ] = (
            "quantity_based_"
            + quantity_mode
        )

        result[
            "should_update_quantity"
        ] = True

        result[
            "should_update_progress"
        ] = True

        result[
            "new_quantity"
        ] = round(
            new_quantity,
            2,
        )

        result[
            "new_progress"
        ] = target_progress

        result[
            "progress_contribution"
        ] = round(
            max(
                0,
                target_progress
                - current_progress,
            ),
            2,
        )

        result[
            "reason"
        ] = (
            f"Physical progress calculated "
            f"from {new_quantity:g} / "
            f"{planned_quantity:g} "
            f"{activity_unit or event_unit or 'units'}."
        )

        return result

    # ---------------------------------------------------------------
    # 4. Status-only update
    # ---------------------------------------------------------------

    if progress_state:

        result[
            "method"
        ] = "status_only"

        result[
            "reason"
        ] = (
            f"Progress state '{progress_state}' "
            "was recorded without measurable "
            "progress evidence. Existing "
            "percentage was preserved."
        )

    return result