""" Swagger tests """
from django.test import Client
from django.test import TestCase


class TestSwaggerDefinitions(TestCase):
    """ Swagger tests """
    def test_swagger(self):
        """ Test if the APIDOCS are rendered, this means its syntax is correct """
        c = Client()
        try:
            response = c.get('/modules/api/v1/apidocs', {'format': 'openapi'})
            self.assertEqual(response.status_code, 301)
        except Exception:  # pragma: no cover
            # Should never happen, it means your swagger definitions are erroneous
            self.assertEqual(True, False)

