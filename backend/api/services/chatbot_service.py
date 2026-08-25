"""Chatbot orchestration: filter extraction → DB fetch → answer generation.

Two-step pipeline per user turn:
  1. extract_query_filters — cheap LLM call, schema + question only, returns JSON filters
  2. fetch_data            — Django ORM query using extracted filters
  3. generate_answer       — LLM call with exact DB rows + rolling conversation history
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime

from api.services import llm_service

# --------------------------------------------------------------------------- #
# Schema prompt used in Step 1 (compact — field names only to minimise tokens)
# --------------------------------------------------------------------------- #

_SCHEMA_PROMPT = """You are a database query assistant for Maersk's WPM (Work Placement Migration) platform.

Tables and key fields:
- migration_intake_submission: migration_request_id, project_name, status, requestor, region, function_name, products, fte_number, jl2, jl3, jl4, risks, requested_date
- opportunity_assessment: migration_request_id, product, owner, location, l1, l2, l3, l4, task_name, task_description, complexity, migratable_to_gsc, risks_related, gsc_site, area, training_time_needed, recommended_handoff_duration, task_frequency, volume_monthly
- approval_workflow: migration_request_id, area_head_status, pmo_status, bpm_budget_status, fbp_status, wpm_review_status, gsc_head_status, elt_status, business_case_submitted_date, area_head_comments, pmo_review_comment, bpm_comment, fbp_comment, wpm_review_comment, gsc_head_comment, elt_comment
- project_gantt_plan: migration_request_id, tasks (JSON list of {id, name, plan:{startWeek,endWeek}, actual, completedAt}), meta (JSON with phase, scope, FTE, HC totals)

Extract query intent from the user's question. Your response must be ONLY a valid JSON object — no explanation, no markdown, no code block, just the raw JSON.

Use this exact structure:
{
  "tables": [],
  "shared_filters": {"migration_request_id": null},
  "intake_filters": {
    "project_name__icontains": null,
    "status__icontains": null,
    "region__icontains": null,
    "requestor__icontains": null,
    "function_name__icontains": null
  },
  "assessment_filters": {
    "complexity__icontains": null,
    "product__icontains": null,
    "migratable_to_gsc__icontains": null,
    "gsc_site__icontains": null,
    "area__icontains": null,
    "l1__icontains": null,
    "l2__icontains": null,
    "task_name__icontains": null
  },
  "approval_filters": {
    "area_head_status__icontains": null,
    "pmo_status__icontains": null,
    "bpm_budget_status__icontains": null,
    "fbp_status__icontains": null,
    "wpm_review_status__icontains": null,
    "gsc_head_status__icontains": null,
    "elt_status__icontains": null
  },
  "gantt_filters": {}
}

Rules:
- "tables" must be a list containing any of: "migration_intake_submission", "opportunity_assessment", "approval_workflow", "project_gantt_plan".
- Set filter values only when the user clearly references that field. Leave all others as null.
- Use "approval_workflow" for questions about approval status, approvals, reviews, business case, ELT, PMO, BPM, FBP, WPM, GSC head, area head.
- Use "project_gantt_plan" for questions about timelines, Gantt, schedule, tasks progress, start/end weeks, completion.
- Use "migration_intake_submission" for project-level questions (status, requestor, region, FTE, risks at project level).
- Use "opportunity_assessment" for task-level questions (complexity, specific tasks, handoff, training).
- shared_filters.migration_request_id: set to the exact ID string if mentioned (e.g. "MR-2024-001")."""

# Fields to strip from serialised DB rows (not useful for LLM context)
_EXCLUDE_FIELDS = {"id", "created_at", "updated_at", "area_country_pairs",
                   "custom_approval_file_name", "custom_approval_file_size",
                   "custom_approval_file_type"}

# Maximum rows returned when no filters are applied
_UNFILTERED_CAP = 50
# Safety cap even for filtered queries (prevents accidental huge contexts)
_FILTERED_CAP = 200


_FALLBACK_SPEC = {
    "tables": ["migration_intake_submission", "opportunity_assessment", "approval_workflow", "project_gantt_plan"],
    "shared_filters": {},
    "intake_filters": {},
    "assessment_filters": {},
    "approval_filters": {},
    "gantt_filters": {},
}


def _parse_json_from_text(text: str) -> dict:
    """Extract a JSON object from LLM output, handling markdown code blocks."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Find the outermost {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError("No JSON object found in LLM response")


def extract_query_filters(question: str) -> dict:
    """Step 1: Ask the LLM to extract DB filter params from the user's question.

    Returns a filter spec dict. Falls back to querying all rows if parsing fails.
    """
    messages = [
        {"role": "system", "content": _SCHEMA_PROMPT},
        {"role": "user", "content": question},
    ]
    try:
        raw = llm_service.chat_completion(messages)
        spec = _parse_json_from_text(raw)
        spec.setdefault("tables", ["migration_intake_submission", "opportunity_assessment", "approval_workflow", "project_gantt_plan"])
        spec.setdefault("shared_filters", {})
        spec.setdefault("intake_filters", {})
        spec.setdefault("assessment_filters", {})
        spec.setdefault("approval_filters", {})
        spec.setdefault("gantt_filters", {})
        return spec
    except Exception:
        return _FALLBACK_SPEC.copy()


def _clean_row(row: dict) -> dict:
    cleaned = {}
    for k, v in row.items():
        if k in _EXCLUDE_FIELDS:
            continue
        if v is None or v == "" or v == [] or v == {}:
            continue
        # Convert datetime/date to ISO string for JSON serialisation
        if isinstance(v, datetime):
            v = v.isoformat()
        elif isinstance(v, date):
            v = v.isoformat()
        cleaned[k] = v
    return cleaned


def fetch_data(filter_spec: dict) -> dict:
    """Query configured tables using extracted filters."""
    from api.models import ApprovalWorkflow, MigrationIntakeSubmission, OpportunityAssessment, ProjectGanttPlan

    tables = filter_spec.get("tables", ["migration_intake_submission", "opportunity_assessment", "approval_workflow", "project_gantt_plan"])
    shared = {k: v for k, v in filter_spec.get("shared_filters", {}).items() if v is not None}
    intake_f = {k: v for k, v in filter_spec.get("intake_filters", {}).items() if v is not None}
    assess_f = {k: v for k, v in filter_spec.get("assessment_filters", {}).items() if v is not None}
    approval_f = {k: v for k, v in filter_spec.get("approval_filters", {}).items() if v is not None}
    gantt_f = {k: v for k, v in filter_spec.get("gantt_filters", {}).items() if v is not None}

    result: dict[str, list] = {
        "migration_intake": [],
        "opportunity_assessment": [],
        "approval_workflow": [],
        "project_gantt_plan": [],
    }

    if "migration_intake_submission" in tables:
        qs = MigrationIntakeSubmission.objects.all()
        combined = {**shared, **intake_f}
        if combined:
            qs = qs.filter(**combined)[:_FILTERED_CAP]
        else:
            qs = qs[:_UNFILTERED_CAP]
        result["migration_intake"] = [_clean_row(r) for r in qs.values()]

    if "opportunity_assessment" in tables:
        qs = OpportunityAssessment.objects.all()
        combined = {**shared, **assess_f}
        if combined:
            qs = qs.filter(**combined)[:_FILTERED_CAP]
        else:
            qs = qs[:_UNFILTERED_CAP]
        result["opportunity_assessment"] = [_clean_row(r) for r in qs.values()]

    if "approval_workflow" in tables:
        qs = ApprovalWorkflow.objects.all()
        combined = {**shared, **approval_f}
        if combined:
            qs = qs.filter(**combined)[:_FILTERED_CAP]
        else:
            qs = qs[:_UNFILTERED_CAP]
        result["approval_workflow"] = [_clean_row(r) for r in qs.values()]

    if "project_gantt_plan" in tables:
        qs = ProjectGanttPlan.objects.all()
        combined = {**shared, **gantt_f}
        if combined:
            qs = qs.filter(**combined)[:_FILTERED_CAP]
        else:
            qs = qs[:_UNFILTERED_CAP]
        result["project_gantt_plan"] = [_clean_row(r) for r in qs.values()]

    return result


def generate_answer(question: str, history: list, data: dict) -> str:
    """Step 2: Ask the LLM to answer the question using the fetched DB records."""
    intake_count = len(data.get("migration_intake", []))
    assess_count = len(data.get("opportunity_assessment", []))
    approval_count = len(data.get("approval_workflow", []))
    gantt_count = len(data.get("project_gantt_plan", []))
    today = date.today().isoformat()

    system_context = (
        "You are a helpful assistant for Maersk's WPM (Work Placement Migration) platform. "
        "Migration managers and leaders use this to track workforce migration projects. "
        "Answer the user's question based ONLY on the database records provided below. "
        "Be concise and structured. Use bullet points for lists, markdown tables for comparisons. "
        "If the data does not contain the answer, say so clearly — never invent information. "
        f"Today's date: {today}."
    )

    data_context = (
        f"Database records — {intake_count} migration project(s), "
        f"{assess_count} opportunity assessment task(s), "
        f"{approval_count} approval workflow record(s), "
        f"{gantt_count} Gantt plan(s):\n"
        + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )

    # Rolling history window — last 6 messages (3 turns)
    recent_history = history[-6:] if len(history) > 6 else history

    messages = (
        [
            {"role": "system", "content": system_context},
            {"role": "system", "content": data_context},
        ]
        + recent_history
        + [{"role": "user", "content": question}]
    )

    return llm_service.chat_completion(messages)


def answer_question(question: str, history: list) -> str:
    """Full pipeline: extract filters → fetch data → generate answer."""
    filter_spec = extract_query_filters(question)
    data = fetch_data(filter_spec)
    return generate_answer(question, history, data)
