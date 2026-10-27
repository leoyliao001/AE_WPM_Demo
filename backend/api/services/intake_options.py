import json
from pathlib import Path


with (Path(__file__).resolve().parent.parent / "data" / "intake_options.json").open(encoding="utf-8") as source:
    INTAKE_OPTIONS = json.load(source)


def validate_intake_selections(project, changes):
    def options_for(mapping, parents):
        return {value for parent in parents for value in mapping.get(parent, [])}

    areas = project.areas or []
    rules = {
        "migration_type": ([item["label"] for item in INTAKE_OPTIONS["migrationTypes"]], set()),
        "region": (INTAKE_OPTIONS["regionAreaMapping"], set()),
        "areas": (INTAKE_OPTIONS["regionAreaMapping"].get(project.region, []), {"region"}),
        "countries": (options_for(INTAKE_OPTIONS["areaCountryMapping"], areas), {"region", "areas"}),
        "function_name": (INTAKE_OPTIONS["functionProductMapping"], set()),
        "products": (INTAKE_OPTIONS["functionProductMapping"].get(project.function_name, []), {"function_name"}),
        "default_location_strategies": (
            {site for area in areas for site in INTAKE_OPTIONS["areaLocationMapping"].get(area, {}).get("supportingSites", [])},
            {"region", "areas", "location_strategy_custom"},
        ),
        "custom_location_strategies": (INTAKE_OPTIONS["customLocationStrategyOptions"], {"location_strategy_custom"}),
    }
    for field, (options, parents) in rules.items():
        if field not in changes and not parents.intersection(changes):
            continue
        if field == "default_location_strategies" and project.location_strategy_custom:
            continue
        if field == "custom_location_strategies" and not project.location_strategy_custom:
            continue
        raw = getattr(project, field)
        values = raw if isinstance(raw, list) else [raw]
        if any(value not in options for value in values):
            raise ValueError(f"{field} contains selections unavailable for the selected parent. Review the Intake choices.")
    if project.location_strategy_custom:
        old_strategy = changes.get("location_strategy_custom", {}).get("old", True)
        old_sites = changes.get("custom_location_strategies", {}).get("old", project.custom_location_strategies)
        if not old_strategy or set(project.custom_location_strategies) - set(old_sites):
            raise ValueError("New custom destination selections require approval at the Intake source before use in Business Case.")
