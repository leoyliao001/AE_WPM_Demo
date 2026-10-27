import hashlib
import json
from datetime import timedelta

from django.utils import timezone

from api.models import ApprovalWorkflow, ProjectGanttPlan, ScopeStatement, StakeholderRegistration
from api.views.project_gantt import merge_gantt_tasks_with_template

LEADERSHIP_ROLES = (
    ("project_sponsor", "Project Sponsor"),
    ("elt", "ELT Sponsor"),
    ("area_poc", "Area POC (Lead)"),
    ("gsc_head_1", "GSC Lead (GSC Head-1)"),
    ("gpl", "GPL"),
    ("wpm_focals", "WPM Focal"),
)
SIGNOFF_ROLES = ("project_sponsor", "elt", "area_functional_leader", "gsc_head_1")
DELIVERABLES = (
    ("initiating", "1 Initiate > TG1",
     "Opportunity assessment approved; scope and final FTE locked; business case approved; governance and integrated plan",
     ("business-case", "fbp-approval", "functional-head", "elt-approval", "gsc-head", "opportunity-assessment", "pid-approval", "hiring-request")),
    ("planning", "2 Plan > TG2",
     "Site readiness (seats, laptops, access); SOPs / IOPs; training and KT framework; wave plans; KPI baselines",
     ("resource-mobilization",)),
    ("executing", "3 Execute > TG3",
     "Hiring and onboarding per wave; training, knowledge transfer and work transfer",
     ("neo-training", "knowledge-transfer", "volume-transfer")),
    ("monitor-control", "4 Monitor & Control > TG4",
     "Hypercare exit per wave against exit criteria",
     ("hypercare", "hypercare-exit")),
    ("closing", "5 Closure > TG5",
     "Area position release; benefits tracking; automation roadmap",
     ("sign-off", "capacity-release")),
)


def build_charter_sources(project):
    from api.views.approval_cycle import _progress
    from api.models import BusinessCase
    from api.services.business_case import build_business_case, online_case_is_approved

    scope = ScopeStatement.objects.filter(project=project).prefetch_related("lines").first()
    registry = StakeholderRegistration.objects.filter(project=project).first()
    plan = ProjectGanttPlan.objects.filter(project=project).first()
    workflow = ApprovalWorkflow.objects.filter(migration_request_id=project.migration_request_id).first()
    members = {person["id"]: person for person in (registry.team_members if registry else [])}
    assignments = registry.assignments if registry else {}

    def assigned_people(code):
        assignment = assignments.get(code, {})
        if not assignment.get("lockedAt") or assignment.get("notApplicable"):
            return []
        return [
            {"name": members[person_id]["fullName"], "email": members[person_id]["email"]}
            for person_id in assignment.get("personIds", [])
            if person_id in members
        ]

    leadership = [
        {"role": code, "label": label, "people": assigned_people(code)}
        for code, label in LEADERSHIP_ROLES
    ]
    signatories = [
        {"role": code, "people": assigned_people(code)}
        for code in SIGNOFF_ROLES
    ]
    lines = list(scope.lines.all()) if scope else []
    scope_locked = bool(
        scope and scope.status == "submitted" and not scope.review_required and scope.final_project_fte is not None
        and {line.job_level for line in lines} == {"JL2", "JL3", "JL4"}
        and all(line.locked_at and line.final_fte is not None for line in lines)
    )
    final_fte = scope.final_project_fte if scope_locked else None
    approval_progress = _progress(workflow) if workflow else None
    business_approved = bool(
        project.business_case_submission_date and approval_progress
        and approval_progress["step"] > approval_progress["seqLen"]
        and approval_progress["completed"]
    )
    online = BusinessCase.objects.filter(project=project).first()
    online_financials = build_business_case(project, online)[2] if online else None
    if online:
        business_approved = online_case_is_approved(project)
    tasks, _ = merge_gantt_tasks_with_template(
        plan.tasks if plan else None, project.created_at, project.business_case_submission_date
    )
    tasks_by_id = {task["id"]: task for task in tasks}
    created_date = timezone.localtime(project.created_at).date()
    start_monday = created_date - timedelta(days=created_date.weekday()) + timedelta(weeks=1)

    def date_range(selected):
        ranges = [task["plan"] for task in selected if task.get("plan")]
        if not ranges:
            return ""
        start = start_monday + timedelta(weeks=min(item["startWeek"] for item in ranges) - 1)
        end = start_monday + timedelta(weeks=max(item["endWeek"] for item in ranges) - 1, days=6)
        return f"{start.isoformat()} - {end.isoformat()}"

    deliverables = []
    for phase_id, label, text, task_ids in DELIVERABLES:
        selected = [tasks_by_id[task_id] for task_id in task_ids if task_id in tasks_by_id]
        complete = len(selected) == len(task_ids) and all(task.get("completedAt") for task in selected)
        started = any(task.get("completedAt") or task.get("actual") for task in selected)
        deliverables.append({
            "id": phase_id, "phase": label, "description": text,
            "timeline": date_range(selected),
            "status": "complete" if complete else "in_progress" if started else "not_started",
        })
    sites = (project.default_location_strategies or []) + (project.custom_location_strategies or [])
    route = f"{', '.join(project.areas or []) or 'Source not provided'} > {', '.join(sites) or 'Destination not provided'}"
    scope_text = scope.scope_text if scope else ""
    vision = f"Deliver {project.project_name}: {scope_text or project.proposed_scope}"
    if final_fte is not None:
        vision += f" Transition {final_fte} locked FTE."
    criteria = []
    if final_fte is not None:
        criteria.append(f"{final_fte} FTE transitioned (locked final Scope Statement FTE).")
    sources = {
        "leadership": leadership,
        "signatories": signatories,
        "facts": [
            {"label": "Migration type", "value": project.migration_type, "source": "Intake"},
            {"label": "Function / Process", "value": " / ".join([project.function_name, ", ".join(project.products or [])]), "source": "Intake"},
            {"label": "Route", "value": route, "source": "Intake"},
            {"label": "Final FTE (locked)", "value": final_fte, "source": "Scope Statement"},
            {"label": "Timeline", "value": date_range(tasks), "source": "Saved Gantt plan"},
            {"label": "Recurring benefit / payback",
             "value": (
                 f"USD {online_financials['metrics']['recurringAnnualBenefit']} / "
                 f"{online_financials['metrics']['paybackMonths'] or 'N/A'} months"
                 if online_financials and online_financials["ready"] else None
             ), "source": "Business Case"},
        ],
        "scope": {"inScope": scope_text, "outOfScope": scope.out_of_scope if scope else None, "assumptions": scope.assumptions if scope else None},
        "deliverables": deliverables,
        "risks": online.details.get("risks") if online else None,
        "dependencies": online.details.get("dependencies") if online else None,
        "fteTimeline": scope.waves if scope else [],
        "autoCriteria": criteria,
        "draftVision": vision[:10000],
        "completeness": [
            {"label": "Scope signed off and final FTE locked", "complete": scope_locked, "source": "scope-statement"},
            {"label": "Business Case approved", "complete": business_approved, "source": "business-case"},
            {"label": "All four sign-off roles locked in Stakeholder Registration", "complete": all(item["people"] for item in signatories), "source": "stakeholder-registration"},
        ],
    }
    fingerprint = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    return sources, fingerprint
