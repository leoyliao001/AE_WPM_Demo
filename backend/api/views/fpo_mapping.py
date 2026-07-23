"""
FPO Mapping API — Handsontable cascade table.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import FpoMapping
from api.permissions.attributes_access import require_attributes_access

# All DB columns (Excel order) for Handsontable headers
ALL_FIELDS = [
    ("l1", "L1"),
    ("gpl", "GPL"),
    ("l2", "L2"),
    ("sfpo", "SFPO"),
    ("num_business_policy", "# of Business Policy"),
    ("l3", "L3"),
    ("fpo", "FPO"),
    ("risk_link", "Risk Link"),
    ("control_link", "Control Link"),
    ("l4", "L4"),
    ("activity_type", "Activity Type"),
    ("sub_process_call_activity", "Sub-Process/Call Activity"),
    ("activity_type_2", "Activity Type (L5)"),
    ("assigned_models_from_l5", "Assigned Models from L5"),
    ("process_level", "Process Level"),
    ("process_grouping", "Process Grouping"),
    ("last_change", "Last change"),
    ("guid", "GUID"),
    ("connect_link", "Connect Link"),
    ("num_automated_activities", "# of Automated activities"),
    ("num_system_supported_activities", "# of System Supported activities"),
    ("num_manual_activities", "# of Manual activities"),
    ("num_undefined_activities", "# of Undefined activities"),
    ("num_sub_process_activities", "# of Sub-Process activities"),
    ("num_ms_office_activities", "# of MS-Office activities"),
    ("num_touchpoint_external_parties", "# of Touchpoint with External parties"),
    ("num_risks", "# of Risks"),
    ("num_controls", "# of Controls"),
    ("num_manual_controls", "# of Manual Controls"),
    ("num_business_rules", "# of Business Rules"),
    ("report_generation_date", "Report Generation Date"),
    ("sharepoint_link_sop", "Sharepoint Link(SOP)"),
]

CASCADE_FIELD_KEYS = {
    "l1",
    "gpl",
    "l2",
    "sfpo",
    "num_business_policy",
    "l3",
    "fpo",
    "risk_link",
    "control_link",
    "l4",
    "activity_type",
    "sub_process_call_activity",
    "activity_type_2",
    "assigned_models_from_l5",
}


def _serialize_row(item: FpoMapping) -> dict:
    return {
        "id": item.id,
        "l1": item.l1,
        "gpl": item.gpl,
        "l2": item.l2,
        "sfpo": item.sfpo,
        "num_business_policy": item.num_business_policy,
        "l3": item.l3,
        "fpo": item.fpo,
        "risk_link": item.risk_link,
        "control_link": item.control_link,
        "l4": item.l4,
        "activity_type": item.activity_type,
        "sub_process_call_activity": item.sub_process_call_activity,
        "activity_type_2": item.activity_type_2,
        "assigned_models_from_l5": item.assigned_models_from_l5,
        "process_level": item.process_level,
        "process_grouping": item.process_grouping,
        "last_change": item.last_change,
        "guid": item.guid,
        "connect_link": item.connect_link,
        "num_automated_activities": item.num_automated_activities,
        "num_system_supported_activities": item.num_system_supported_activities,
        "num_manual_activities": item.num_manual_activities,
        "num_undefined_activities": item.num_undefined_activities,
        "num_sub_process_activities": item.num_sub_process_activities,
        "num_ms_office_activities": item.num_ms_office_activities,
        "num_touchpoint_external_parties": item.num_touchpoint_external_parties,
        "num_risks": item.num_risks,
        "num_controls": item.num_controls,
        "num_manual_controls": item.num_manual_controls,
        "num_business_rules": item.num_business_rules,
        "report_generation_date": item.report_generation_date,
        "sharepoint_link_sop": item.sharepoint_link_sop,
    }


def _build_cascade_tree(rows: list[dict]) -> dict:
    """Nested lookup for Handsontable cascading dropdowns."""
    tree: dict = {"l1_list": [], "by_l1": {}}

    def _unique_append(lst: list, value: str) -> None:
        if value and value not in lst:
            lst.append(value)

    for r in rows:
        l1 = r["l1"] or ""
        if not l1:
            continue

        if l1 not in tree["by_l1"]:
            tree["by_l1"][l1] = {
                "gpl": r["gpl"] or "",
                "l2_list": [],
                "by_l2": {},
            }
            tree["l1_list"].append(l1)

        n1 = tree["by_l1"][l1]
        if r["gpl"] and not n1["gpl"]:
            n1["gpl"] = r["gpl"]

        l2 = r["l2"] or ""
        if not l2:
            continue

        if l2 not in n1["by_l2"]:
            n1["by_l2"][l2] = {
                "sfpo": r["sfpo"] or "",
                "num_business_policy": r["num_business_policy"] or "",
                "l3_list": [],
                "by_l3": {},
            }
            n1["l2_list"].append(l2)

        n2 = n1["by_l2"][l2]
        if r["sfpo"] and not n2["sfpo"]:
            n2["sfpo"] = r["sfpo"]
        if r["num_business_policy"] and not n2["num_business_policy"]:
            n2["num_business_policy"] = r["num_business_policy"]

        l3 = r["l3"] or ""
        if not l3:
            continue

        if l3 not in n2["by_l3"]:
            n2["by_l3"][l3] = {
                "fpo": r["fpo"] or "",
                "risk_link": r["risk_link"] or "",
                "control_link": r["control_link"] or "",
                "l4_list": [],
                "by_l4": {},
            }
            n2["l3_list"].append(l3)

        n3 = n2["by_l3"][l3]
        if r["fpo"] and not n3["fpo"]:
            n3["fpo"] = r["fpo"]
        if r["risk_link"] and not n3["risk_link"]:
            n3["risk_link"] = r["risk_link"]
        if r["control_link"] and not n3["control_link"]:
            n3["control_link"] = r["control_link"]

        l4 = r["l4"] or ""
        if not l4:
            continue

        if l4 not in n3["by_l4"]:
            n3["by_l4"][l4] = {
                "activity_type_list": [],
                "sub_process_list": [],
                "by_sub_process": {},
            }
            n3["l4_list"].append(l4)

        n4 = n3["by_l4"][l4]
        _unique_append(n4["activity_type_list"], r["activity_type"] or "")

        sub = r["sub_process_call_activity"] or ""
        if not sub:
            continue

        _unique_append(n4["sub_process_list"], sub)
        if sub not in n4["by_sub_process"]:
            n4["by_sub_process"][sub] = {
                "activity_type_2": r["activity_type_2"] or "",
                "assigned_models_from_l5": r["assigned_models_from_l5"] or "",
            }
        else:
            leaf = n4["by_sub_process"][sub]
            if r["activity_type_2"] and not leaf["activity_type_2"]:
                leaf["activity_type_2"] = r["activity_type_2"]
            if r["assigned_models_from_l5"] and not leaf["assigned_models_from_l5"]:
                leaf["assigned_models_from_l5"] = r["assigned_models_from_l5"]

    return tree


@api_view(["GET"])
@require_attributes_access("fpo_mapping")
def list_fpo_mapping(request):
    """GET /api/fpo-mapping/ — all DB rows for the grid + cascade tree."""
    qs = FpoMapping.objects.all().order_by("id")
    rows = [_serialize_row(item) for item in qs]

    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "cascade_keys": sorted(CASCADE_FIELD_KEYS),
            "cascade": _build_cascade_tree(rows),
            "rows": rows,
        }
    )
