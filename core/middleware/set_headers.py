class DefaultHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.endswith(".ics"):
            # Leave caching to the view
            return response
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        if response.get("Content-Type"):
            if "charset" not in response["Content-Type"]:
                response["Content-Type"] += "; charset=UTF-8"
        else:
            response["Content-Type"] = "application/json; charset=UTF-8"
        return response
