from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(request):
    """GET /api/health/ — system health check."""
    return Response({"status": "ok", "message": "AE WPM Demo API is running"})
