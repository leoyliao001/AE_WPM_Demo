from django.urls import include, path

urlpatterns = [
    path("health/", include("api.routes.health")),
    path("future-service-model/", include("api.routes.future_service_model")),
    path("migration-intake/", include("api.routes.migration_intake")),
    path("migration-dashboard/", include("api.routes.migration_dashboard")),
    path("ld-dashboard/", include("api.routes.ld_dashboard")),
    path("project-dashboard/", include("api.routes.project_dashboard")),
    path("migration-chatbot/", include("api.routes.migration_chatbot")),
    path("fpo-mapping/", include("api.routes.fpo_mapping")),
    path("product-ownership/", include("api.routes.product_ownership")),
    path("gsc-site-mapping/", include("api.routes.gsc_site_mapping")),
]
