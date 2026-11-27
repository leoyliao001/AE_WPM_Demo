from django.urls import path

from api.views.baseline_kpis_admin import (
    baseline_kpi_record_detail,
    baseline_kpi_records,
)

urlpatterns = [
    path("", baseline_kpi_records, name="baseline-kpi-records"),
    path("<int:record_id>/", baseline_kpi_record_detail, name="baseline-kpi-record-detail"),
]
