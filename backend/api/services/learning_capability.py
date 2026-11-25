import json
import math


MAX_STATE_BYTES = 5 * 1024 * 1024


def _number(value):
    if isinstance(value, bool):
        return 0
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0
    return number if math.isfinite(number) else 0


def _validate_json_value(value, depth=0):
    if depth > 12:
        raise ValueError("Learning data is nested too deeply.")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        if len(value) > 20000:
            raise ValueError("A learning data field exceeds 20000 characters.")
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Learning data must contain finite numbers.")
        return
    if isinstance(value, list):
        if len(value) > 10000:
            raise ValueError("A learning data list is too large.")
        for item in value:
            _validate_json_value(item, depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > 10000:
            raise ValueError("A learning data object is too large.")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 255:
                raise ValueError("Learning data keys must be strings of 255 characters or fewer.")
            _validate_json_value(item, depth + 1)
        return
    raise ValueError("Learning data must contain JSON values only.")


def validate_learning_state(raw):
    if not isinstance(raw, dict):
        raise ValueError("Learning state must be an object.")
    state = {
        "plans": raw.get("plans", {}),
        "kt": raw.get("kt", {}),
        "scores": raw.get("scores", {}),
        "processCount": raw.get("processCount", 0),
    }
    if any(not isinstance(state[key], dict) for key in ("plans", "kt", "scores")):
        raise ValueError("Learning plans, KT entries and scores must be objects.")
    process_count = state["processCount"]
    if isinstance(process_count, bool) or not isinstance(process_count, int) or not 0 <= process_count <= 50000:
        raise ValueError("Process count must be a non-negative integer.")
    _validate_json_value(state)
    if len(json.dumps(state, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_STATE_BYTES:
        raise ValueError("Learning state exceeds the 5 MB limit.")
    return state


def learning_progress_summary(state=None, evidence_present=False):
    state = state if isinstance(state, dict) else {}
    plans = state.get("plans") if isinstance(state.get("plans"), dict) else {}
    kt = state.get("kt") if isinstance(state.get("kt"), dict) else {}
    scores = state.get("scores") if isinstance(state.get("scores"), dict) else {}
    cohorts = list(plans.values())
    raw_process_count = state.get("processCount")
    process_count = raw_process_count if isinstance(raw_process_count, int) and not isinstance(raw_process_count, bool) and raw_process_count > 0 else 6
    kt_rows = [
        row
        for cohort_rows in kt.values()
        if isinstance(cohort_rows, dict)
        for row in cohort_rows.values()
        if isinstance(row, dict)
    ]
    kt_cells = []
    for row in kt_rows:
        l4_rows = row.get("l4") if isinstance(row.get("l4"), dict) else {}
        if row.get("expanded"):
            kt_cells.extend(item for item in l4_rows.values() if isinstance(item, dict))
        else:
            kt_cells.append(row)
    score_rows = [
        row
        for cohort_scores in scores.values()
        if isinstance(cohort_scores, list)
        for row in cohort_scores
        if isinstance(row, dict)
    ]
    straight_to_kt = not any(
        isinstance(plan, dict) and _number(plan.get("fdays")) > 0
        for plan in cohorts
    )
    complete_scores = [
        row for row in score_rows
        if row.get("kt") not in ("", None)
        and (row.get("foundation") not in ("", None) or straight_to_kt)
    ]
    updated_cohorts = sum(
        1 for plan in cohorts
        if isinstance(plan, dict) and plan.get("start") and plan.get("fdays") != "" and plan.get("trainer")
    )
    denominator = max(1, len(kt) * process_count)
    return {
        "stages": [
            round(updated_cohorts / len(cohorts) * 100) if cohorts else 0,
            min(100, round(sum(bool(row.get("deliveredBy")) for row in kt_cells) / denominator * 100)),
            min(100, round(sum(row.get("material") == "Ready" for row in kt_cells) / denominator * 100)),
            round(len(complete_scores) / len(score_rows) * 100) if score_rows else 0,
            100 if evidence_present else 0,
        ],
        "gaps": sum(row.get("deliveredBy") == "Not able to deliver" for row in kt_cells),
        "cohorts": len(cohorts),
    }
