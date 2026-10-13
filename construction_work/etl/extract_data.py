"""
Fetch all project and article data from DvO via its API
"""

from construction_work.etl.queries import PROJECTS_WITH_DETAILS
from core.utils.dvo_utils import DvOClient


class ConstructionWorkService(DvOClient):
    pass


def get_all_drupal_projects_with_content():
    """
    Fetch all construction work projects and their content from DvO via GraphQL.

    The query is paginated and expects the client to provide the ``page``
    variable for each request.
    """
    query = PROJECTS_WITH_DETAILS

    with ConstructionWorkService() as client:
        return client.fetch_all(
            query,
            get_pagination=lambda data: data["view"]["pagination"],
            get_nodes=lambda data: data["view"]["nodes"],
        )
