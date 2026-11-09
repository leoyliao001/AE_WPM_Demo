from api.models import ServiceCatalogue


OPPORTUNITY_CATALOGUE_NAME = "Catalogue_OtC_Comprehensive V1.6"


def load_opportunity_catalogue():
    return [
        list(row)
        for row in ServiceCatalogue.objects.filter(catalogue=OPPORTUNITY_CATALOGUE_NAME)
        .order_by("id")
        .values_list(
            "product",
            "l1",
            "l2",
            "l3",
            "l4",
            "direction",
            "current_ownership",
            "average_handle_time",
            "task_name",
        )
    ]