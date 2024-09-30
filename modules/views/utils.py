from modules.api_messages import Messages
from modules.models import ModuleVersion

message = Messages()


def slug_status_in_releases(slug) -> dict:
    """
    Get status in releases

    Returns: {"1.2.3": [{"status": 1, "releases": ["0.0.1"]}]}
    """
    module_versions = ModuleVersion.objects.filter(module__slug=slug).all()

    slug_status_in_releases = {}
    for _version in module_versions:
        rms_all = _version.releasemodulestatus_set.all()
        status_in_releases = {}
        for rms in rms_all:
            if rms.status in status_in_releases:
                status_in_releases[rms.status]["releases"].append(
                    rms.app_release.version
                )
            else:
                status_in_releases[rms.status] = {"releases": [rms.app_release.version]}

            slug_status_in_releases[_version.version] = [
                {"status": k, "releases": v["releases"]}
                for k, v in status_in_releases.items()
            ]

    return slug_status_in_releases


def version_number_as_list(version: str):
    return [int(x) for x in version.split(".")]
