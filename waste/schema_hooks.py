def add_pdf_endpoint(endpoints):
    from waste.views.waste_views import WasteGuidePDFSchemaView

    endpoints.append(
        (
            "/waste/api/v1/guide/pdf",  # path
            r"^/waste/api/v1/guide/pdf$",  # regex
            "GET",  # method
            WasteGuidePDFSchemaView.as_view(),  # callback
        )
    )

    return endpoints


def add_ics_endpoint(endpoints):
    from waste.views.waste_views import WasteGuideCalendarIcsSchemaView

    endpoints.append(
        (
            "/waste/api/v1/guide/{bag_nummeraanduiding_id}.ics",  # path
            r"^/waste/api/v1/guide/(?P<bag_nummeraanduiding_id>[^/.]+)\.ics$",  # regex
            "GET",  # method
            WasteGuideCalendarIcsSchemaView.as_view(),  # callback
        )
    )

    return endpoints
