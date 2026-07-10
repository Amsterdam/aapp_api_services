from unittest.mock import patch

from django.test import SimpleTestCase

from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    FilterClass,
    IconClass,
    LayerClass,
    ListPropertyClass,
    PropertiesClass,
)
from contact.services.event_abstract import EventAbstractService


class DummyData(ChoicesEnum):
    FIRST = DataLayer(label="First", code=1, icon_label="first")
    SECOND = DataLayer(label="Second", code=2, icon_label="second")


class DummyFilters(ChoicesEnum):
    FIRST = FilterClass(label="First", filter_key="aapp_subtitle", filter_value="First")


class DummyLayers(ChoicesEnum):
    FIRST = LayerClass(
        label="First",
        filter_key="aapp_subtitle",
        filter_value="First",
        icon_label="first",
    )


class DummyProperties(ChoicesEnum):
    ADDRESS = PropertiesClass(
        label="Adres",
        property_key="aapp_address",
        property_type="address",
        icon=None,
    )


class DummySilentProperties(ChoicesEnum):
    FILL = PropertiesClass(
        label=None,
        property_key="fill",
        property_type="string",
        icon=None,
    )


class DummyIcons(ChoicesEnum):
    FIRST = IconClass(
        label="first",
        path="M0,0",
        path_color="#000000",
        circle_color="#ffffff",
    )


class DummyEventService(EventAbstractService):
    data_enum = DummyData
    filters_enum = DummyFilters
    layers_enum = DummyLayers
    properties_enum = DummyProperties
    silent_properties_enum = DummySilentProperties
    icons_enum = DummyIcons
    list_property = ListPropertyClass(key="aapp_subtitle", type="string")


class EventAbstractServiceTest(SimpleTestCase):
    def setUp(self):
        self.service = DummyEventService()

    def test_init_requires_enums(self):
        class MissingData(EventAbstractService):
            filters_enum = DummyFilters
            layers_enum = DummyLayers
            properties_enum = DummyProperties

        class MissingFilters(EventAbstractService):
            data_enum = DummyData
            layers_enum = DummyLayers
            properties_enum = DummyProperties

        class MissingLayers(EventAbstractService):
            data_enum = DummyData
            filters_enum = DummyFilters
            properties_enum = DummyProperties

        class MissingProperties(EventAbstractService):
            data_enum = DummyData
            filters_enum = DummyFilters
            layers_enum = DummyLayers

        with self.assertRaises(NotImplementedError):
            MissingData()
        with self.assertRaises(NotImplementedError):
            MissingFilters()
        with self.assertRaises(NotImplementedError):
            MissingLayers()
        with self.assertRaises(NotImplementedError):
            MissingProperties()

    def test_layer_url(self):
        url = self.service._layer_url(
            base_url="https://example.com/", layer={"code": 9}
        )
        self.assertEqual(url, "https://example.com/9.json")

    def test_get_full_data_adds_custom_properties_and_incremental_ids(self):
        self.service.data_layers = [
            {"label": "First", "code": 1, "icon_label": "first"},
            {"label": "Second", "code": 2, "icon_label": "second"},
        ]

        first_layer = [
            {
                "geometry": {"type": "Point", "coordinates": [4.89, 52.37]},
                "properties": {
                    "title": "First title",
                    "description": "<p>desc</p>",
                    "street": "Dam",
                    "street_number": "1",
                    "zip": "1012JS",
                },
            }
        ]
        second_layer = [
            {
                "geometry": {"type": "Point", "coordinates": [4.91, 52.38]},
                "properties": {"title": "Second title"},
            }
        ]

        with patch.object(
            self.service,
            "_get_geojson_items_for_url",
            side_effect=[first_layer, second_layer],
        ):
            full_data = self.service.get_full_data()

        features = full_data["data"]["features"]
        self.assertEqual([feature["id"] for feature in features], [1, 2])
        self.assertEqual(features[0]["properties"]["aapp_subtitle"], "First")
        self.assertEqual(features[1]["properties"]["aapp_subtitle"], "Second")
        self.assertEqual(features[0]["properties"]["aapp_description"], "desc")

    def test_get_full_data_skips_layer_when_fetch_fails(self):
        self.service.data_layers = [
            {"label": "First", "code": 1, "icon_label": "first"},
            {"label": "Second", "code": 2, "icon_label": "second"},
        ]

        second_layer = [
            {
                "geometry": {"type": "Point", "coordinates": [4.91, 52.38]},
                "properties": {"title": "Only feature"},
            }
        ]

        with patch.object(
            self.service,
            "_get_geojson_items_for_url",
            side_effect=[Exception("Fetch failed"), second_layer],
        ):
            full_data = self.service.get_full_data()

        features = full_data["data"]["features"]
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]["id"], 1)

    def test_get_geojson_items_for_url_restores_data_url_on_success(self):
        original_url = self.service.data_url

        with patch.object(self.service, "get_geojson_items", return_value=[{"id": 1}]):
            result = self.service._get_geojson_items_for_url(
                "https://example.com/1.json"
            )

        self.assertEqual(result, [{"id": 1}])
        self.assertEqual(self.service.data_url, original_url)

    def test_get_geojson_items_for_url_restores_data_url_on_error(self):
        original_url = self.service.data_url

        with patch.object(
            self.service, "get_geojson_items", side_effect=RuntimeError("x")
        ):
            with self.assertRaises(RuntimeError):
                self.service._get_geojson_items_for_url("https://example.com/1.json")

        self.assertEqual(self.service.data_url, original_url)

    def test_clean_html(self):
        self.assertEqual(self.service._clean_html(None), "")
        self.assertEqual(self.service._clean_html("<p>Hello</p>"), "Hello")

    def test_get_address_from_properties_point(self):
        address = self.service._get_address_from_properties(
            {"street": "Dam", "street_number": "1", "zip": "1012JS"},
            {"type": "Point", "coordinates": [4.9, 52.3]},
        )
        self.assertEqual(address["coordinates"]["lat"], 52.3)
        self.assertEqual(address["coordinates"]["lon"], 4.9)
        self.assertEqual(address["city"], "Amsterdam")

    def test_get_address_from_properties_multipoint(self):
        address = self.service._get_address_from_properties(
            {},
            {"type": "MultiPoint", "coordinates": [[4.91, 52.31], [4.92, 52.32]]},
        )
        self.assertEqual(address["coordinates"]["lat"], 52.31)
        self.assertEqual(address["coordinates"]["lon"], 4.91)

    def test_get_address_from_properties_invalid_multipoint(self):
        with self.assertLogs("contact.services.event_abstract", level="ERROR"):
            address = self.service._get_address_from_properties(
                {},
                {"type": "MultiPoint", "coordinates": []},
            )
        self.assertEqual(address["coordinates"]["lat"], None)
        self.assertEqual(address["coordinates"]["lon"], None)

    def test_get_address_from_properties_polygon(self):
        address = self.service._get_address_from_properties(
            {},
            {
                "type": "Polygon",
                "coordinates": [[[4.93, 52.33], [4.94, 52.34], [4.95, 52.35]]],
            },
        )
        self.assertEqual(address["coordinates"]["lat"], 52.33)
        self.assertEqual(address["coordinates"]["lon"], 4.93)

    def test_get_address_from_properties_invalid_polygon(self):
        with self.assertLogs("contact.services.event_abstract", level="ERROR"):
            address = self.service._get_address_from_properties(
                {},
                {"type": "Polygon", "coordinates": []},
            )
        self.assertEqual(address["coordinates"]["lat"], None)
        self.assertEqual(address["coordinates"]["lon"], None)

    def test_get_address_from_properties_multipolygon(self):
        address = self.service._get_address_from_properties(
            {},
            {
                "type": "MultiPolygon",
                "coordinates": [[[[4.96, 52.36], [4.97, 52.37], [4.98, 52.38]]]],
            },
        )
        self.assertEqual(address["coordinates"]["lat"], 52.36)
        self.assertEqual(address["coordinates"]["lon"], 4.96)

    def test_get_address_from_properties_invalid_multipolygon(self):
        with self.assertLogs("contact.services.event_abstract", level="ERROR"):
            address = self.service._get_address_from_properties(
                {},
                {"type": "MultiPolygon", "coordinates": []},
            )
        self.assertEqual(address["coordinates"]["lat"], None)
        self.assertEqual(address["coordinates"]["lon"], None)

    def test_get_address_from_properties_unexpected_geometry(self):
        with self.assertLogs("contact.services.event_abstract", level="ERROR"):
            address = self.service._get_address_from_properties(
                {},
                {"type": "LineString", "coordinates": [[4.9, 52.3], [4.91, 52.31]]},
            )
        self.assertEqual(address["coordinates"]["lat"], None)
        self.assertEqual(address["coordinates"]["lon"], None)

    def test_get_website(self):
        self.assertEqual(
            self.service._get_website({"website": "https:\\/\\/example.com"}),
            "https://example.com",
        )
        self.assertEqual(self.service._get_website({"website": "not a url"}), None)
        self.assertEqual(self.service._get_website({}), None)

    def test_create_table(self):
        self.assertEqual(self.service._create_table([]), None)
        self.assertEqual(self.service._create_table(None), None)

        table = self.service._create_table(
            [
                {"title": "Open", "value": "Yes"},
                {"title": "Missing value"},
                {"value": "Missing title"},
            ]
        )

        self.assertEqual(table, [{"key": "Open", "value": "Yes"}])
