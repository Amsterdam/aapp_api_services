""" Swagger tests """

from django.test import Client, TestCase


class TestSwaggerDefinitions(TestCase):
    """Swagger tests"""

    def test_swagger(self):
        """Test if the OPENAPI is rendered, this means its syntax is correct"""
        c = Client()
        response = c.get("/modules/api/v1/openapi", {"format": "openapi"})
        self.assertEqual(301, response.status_code)
