def get_base_url(request, path=""):
    base_url = f"{request.scheme}://{request.get_host()}/{path}"
    return base_url


def get_media_url(request):
    media_url = get_base_url(request, "construction-work/media/")
    return media_url
