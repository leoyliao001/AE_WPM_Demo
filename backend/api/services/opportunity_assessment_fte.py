from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


FREQUENCIES = {
    "Daily": Decimal("21"),
    "Weekly": Decimal("4.33"),
    "Monthly": Decimal("1"),
    "Quarterly": Decimal("1") / Decimal("3"),
    "Yearly": Decimal("1") / Decimal("12"),
    "Ad hoc": Decimal("1"),
}
PRODUCTIVE_HOURS = Decimal("140")


def _decimal(value):
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number.is_finite() else None


def calculate_task_fte(row):
    volume = _decimal(row.get("vol"))
    minutes = _decimal(row.get("tpu"))
    factor = FREQUENCIES.get(row.get("freq"))
    if volume is None or minutes is None or volume <= 0 or minutes <= 0 or factor is None:
        return None
    return volume * minutes * factor / Decimal("60") / PRODUCTIVE_HOURS


def calculate_migratable_fte(state):
    if not isinstance(state, dict):
        return Decimal("0.00")

    mode = state.get("mode")
    if mode == "cat":
        groups = state.get("catGroups")
        rows = (
            [row for group in groups if isinstance(group, dict) for row in group.get("rows", [])]
            if isinstance(groups, list)
            else state.get("cat") or []
        )
    elif mode == "task":
        rows = state.get("task") or []
    else:
        rows = []

    total = Decimal("0")
    for row in rows:
        if not isinstance(row, dict):
            continue
        if mode == "cat" and row.get("mgsc") != "Yes":
            continue
        row_fte = calculate_task_fte(row)
        if row_fte is not None:
            total += row_fte

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
