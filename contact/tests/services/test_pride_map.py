from django.test import SimpleTestCase

from contact.services.pride_map import PrideMapService


class PrideMapServiceTest(SimpleTestCase):
    def setUp(self):
        self.service = PrideMapService()

    def test_preprocess_feature_multipoint_to_point(self):
        feature = {
            "geometry": {
                "type": "MultiPoint",
                "coordinates": [[4.89, 52.37], [4.9, 52.38]],
            },
            "properties": {"id": "x"},
        }

        self.service._preprocess_feature(
            feature=feature,
            layer={"label": "Evenement"},
        )

        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertEqual(feature["geometry"]["coordinates"], [4.89, 52.37])

    def test_preprocess_feature_keeps_geometry(self):
        feature = {
            "geometry": {"type": "Point", "coordinates": [4.89, 52.37]},
            "properties": {"id": "x"},
        }

        self.service._preprocess_feature(
            feature=feature,
            layer={"label": "Evenement"},
        )

        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertEqual(feature["geometry"]["coordinates"], [4.89, 52.37])

    def test_get_custom_properties_default_layer(self):
        properties = {
            "title": "Event",
            "description": "<p>Desc</p>",
            "street": "Damrak",
            "street_number": "1",
            "zip": "1012LG",
            "city": "Amsterdam",
            "website": "https:\\/\\/example.org",
            "meta": [{"title": "Type", "value": "Muziek"}],
        }
        geom = {"type": "Point", "coordinates": [4.9, 52.3]}

        custom = self.service.get_custom_properties(
            properties=properties,
            geom=geom,
            layer_type="Evenement",
            icon_name="event",
        )

        self.assertEqual(custom["aapp_title"], "Event")
        self.assertEqual(custom["aapp_subtitle"], "Evenement")
        self.assertEqual(custom["aapp_description"], "Desc")
        self.assertEqual(custom["aapp_website"], "https://example.org")
        self.assertEqual(custom["aapp_address"]["coordinates"]["lat"], 52.3)
        self.assertEqual(custom["aapp_address"]["coordinates"]["lon"], 4.9)
        self.assertEqual(custom["aapp_table"], [{"key": "Type", "value": "Muziek"}])
        self.assertEqual(custom["stroke"], None)

    def test_get_custom_properties_canal_parade_linestring_stroke(self):
        custom = self.service.get_custom_properties(
            properties={"title": "Parade"},
            geom={"type": "LineString", "coordinates": [[4.9, 52.3], [4.91, 52.31]]},
            layer_type="Canal parade",
            icon_name="canal_parade",
        )

        self.assertEqual(custom["stroke"], "#009DE6")
        self.assertEqual(custom["stroke-width"], 5)

    def test_get_custom_properties_without_street_has_no_address(self):
        custom = self.service.get_custom_properties(
            properties={"title": "No street", "meta": []},
            geom={"type": "Point", "coordinates": [4.9, 52.3]},
            layer_type="Evenement",
            icon_name="event",
        )

        self.assertEqual(custom["aapp_address"], None)
        self.assertEqual(custom["aapp_table"], None)
