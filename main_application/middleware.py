from django.http import JsonResponse

from main_application import settings


class ApiKeyMiddleware:
	def __init__(self, get_response):
		assert settings.API_AUTH_TOKENS, "API_AUTH_TOKENS not set"
		assert settings.MIJN_AMS_AUTH_TOKENS, "MIJN_AMSTERDAM_AUTH_TOKENS not set"
		assert settings.API_AUTH_TOKENS != settings.MIJN_AMS_AUTH_TOKENS, "API_AUTH_TOKENS and MIJN_AMSTERDAM_AUTH_TOKENS must be different"

		self.get_response = get_response

		# Define the default API key
		self.default_api_keys = settings.API_AUTH_TOKENS

		# Define specific API keys for particular endpoints
		self.specific_api_keys = settings.SPECIFIC_API_KEYS

	def __call__(self, request):
		api_key = request.headers.get("X-Api-Key")
		path = request.path_info

		# Check if the endpoint has a specific API key defined
		expected_api_keys = self.specific_api_keys.get(path, self.default_api_keys)
		if not expected_api_keys:
			return JsonResponse({"error": "Authentication not available"}, status=500)
		expected_api_keys = expected_api_keys.split(",")

		# Validate the provided API key
		if api_key not in expected_api_keys:
			return JsonResponse({"error": "Invalid API Key"}, status=403)

		# Proceed to the view if the API key is correct
		response = self.get_response(request)
		return response
