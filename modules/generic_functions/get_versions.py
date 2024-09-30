from modules.models import AppRelease


class VersionQueries:
    @staticmethod
    def get_highest_version(versions: list[str]):
        """Get the latest version from a list of versions
        e.g from ["1.2.3", "2.0.0", "1.5.8"] it returns "2.0.0"
        """

        def version_to_tuple(version):
            return tuple(map(int, version.split(".")))

        return max(versions, key=version_to_tuple)

    @staticmethod
    def get_highest_published_release() -> AppRelease | None:
        """
        Gets the highest published release.
        """
        published_releases = AppRelease.objects.filter(published__isnull=False)
        highest_version = VersionQueries.get_highest_version(
            [x.version for x in published_releases]
        )
        return published_releases.get(version=highest_version)
