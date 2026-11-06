from decimal import Decimal, InvalidOperation

from api.models import OpportunityAssessmentScope


def opportunity_fte_totals(project):
    assessment = OpportunityAssessmentScope.objects.filter(project=project).only("state", "revision").first()
    totals = {
        "assessed": Decimal("0"),
        "migratable": Decimal("0"),
        "exception": Decimal("0"),
        "unclassified": Decimal("0"),
        "available": assessment is not None,
        "revision": assessment.revision if assessment else 0,
    }
    if assessment is None:
        return totals

    state = assessment.state
    if not isinstance(state, dict):
        raise ValueError("Saved Opportunity Assessment state is invalid.")
    mode = state.get("mode")
    if mode in (None, ""):
        rows = []
    elif isinstance(mode, str) and mode in {"cat", "task"}:
        rows = state.get(mode)
    else:
        raise ValueError("Saved Opportunity Assessment mode is invalid.")
    if not isinstance(rows, list):
        raise ValueError("Saved Opportunity Assessment rows are invalid.")

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("Saved Opportunity Assessment row is invalid.")
        classification = row.get("mgsc")
        if classification not in ("Yes", "No", "", None):
            raise ValueError("Saved Opportunity Assessment migration classification is invalid.")
        value = row.get("fte")
        if value in ("", None):
            fte = Decimal("0")
        else:
            try:
                fte = Decimal(str(value))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("Saved Opportunity Assessment FTE is invalid.") from exc
            if not fte.is_finite() or fte < 0:
                raise ValueError("Saved Opportunity Assessment FTE is invalid.")

        totals["assessed"] += fte
        if classification == "Yes":
            totals["migratable"] += fte
        elif classification == "No":
            totals["exception"] += fte
        elif classification in ("", None):
            totals["unclassified"] += fte

    return totals
