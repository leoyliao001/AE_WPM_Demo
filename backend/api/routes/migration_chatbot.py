from django.urls import path

from api.views.migration_chatbot import chat_message

urlpatterns = [
    path("chat/", chat_message, name="migration-chatbot-message"),
]
