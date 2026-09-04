from datetime import datetime

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ExecutiveSummaryNote
from api.permissions.attributes_access import require_any_attributes_access

SECTION_TITLES = {
    "highlights": "Highlights",
    "focus": "Focus",
    "levers": "Levers",
}

DEFAULT_BODIES = {
    "highlights": "Focus on the projects that are already delivering value and on the portfolio areas where speed of execution is improving the most.",
    "focus": "Prioritize the current bottlenecks, manage at-risk programs, and keep the pipeline moving through the approved migration flow.",
    "levers": "Use regional and product-level filters to isolate the biggest gap, then coordinate change management and delivery support where the impact is largest.",
}


def _coerce_year(value, fallback=None):
    try:
        year_num = int(value)
    except (TypeError, ValueError):
        return int(fallback or datetime.now().year)
    return year_num if year_num > 0 else int(fallback or datetime.now().year)


def _serialize_note(item: ExecutiveSummaryNote) -> dict:
    return {
        "id": item.id,
        "section": item.section,
        "year": item.year,
        "title": item.title or SECTION_TITLES.get(item.section, item.section.title()),
        "body": item.body or DEFAULT_BODIES.get(item.section, ""),
    }


@api_view(["GET"])
def list_executive_summary_notes(request):
    year = _coerce_year(request.GET.get("year"), datetime.now().year)
    rows = list(ExecutiveSummaryNote.objects.filter(year=year).order_by("section"))
    notes = [_serialize_note(item) for item in rows]
    by_section = {note["section"]: note for note in notes}
    for section in ("highlights", "focus", "levers"):
        if section not in by_section:
            notes.append(
                {
                    "id": None,
                    "section": section,
                    "year": year,
                    "title": SECTION_TITLES.get(section, section.title()),
                    "body": DEFAULT_BODIES.get(section, ""),
                }
            )
    return Response({"year": year, "notes": sorted(notes, key=lambda item: ["highlights", "focus", "levers"].index(item["section"]))})


@api_view(["POST"])
@require_any_attributes_access("bpm_rofo", "bpm_actual")
def save_executive_summary_notes(request):
    year = _coerce_year(request.data.get("year"), datetime.now().year)
    section = str(request.data.get("section") or "").strip().lower()
    body = str(request.data.get("body") or "").strip()
    title = str(request.data.get("title") or SECTION_TITLES.get(section, section.title())).strip()

    if not section:
        return Response({"error": "section is required."}, status=status.HTTP_400_BAD_REQUEST)
    if section not in SECTION_TITLES:
        return Response({"error": "Unsupported section."}, status=status.HTTP_400_BAD_REQUEST)

    obj, _created = ExecutiveSummaryNote.objects.get_or_create(
        year=year,
        section=section,
        defaults={"title": title, "body": body or DEFAULT_BODIES.get(section, "")},
    )
    obj.title = title or SECTION_TITLES.get(section, section.title())
    obj.body = body or DEFAULT_BODIES.get(section, "")
    obj.save(update_fields=["title", "body", "updated_at"])
    return Response({"status": "success", "note": _serialize_note(obj)})
