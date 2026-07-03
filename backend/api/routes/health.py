from django.urls import path

from api.views import health

urlpatterns = [
    path("", health, name="health"),
]
