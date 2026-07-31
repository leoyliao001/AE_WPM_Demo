"""
Migration chatbot API views.

Frontend page: /migration-chatbot
Endpoint: POST /api/migration-chatbot/chat/
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.services import chatbot_service


@api_view(["POST"])
def chat_message(request):
    question = (request.data.get("question") or "").strip()
    if not question:
        return Response({"error": "question is required"}, status=400)

    history = request.data.get("history") or []
    if not isinstance(history, list):
        history = []

    try:
        answer = chatbot_service.answer_question(question, history)
        return Response({"answer": answer})
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)
