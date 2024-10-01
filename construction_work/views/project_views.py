from datetime import datetime, timedelta
from math import ceil

from django.conf import settings
from django.db.models import DateTimeField, Max, Value
from django.db.models.functions import Coalesce, Greatest
from rest_framework import generics, status
from rest_framework.response import Response

from construction_work.models import Article, Device, Project, WarningMessage
from construction_work.serializers import ProjectExtendedSerializer
from construction_work.utils import address_to_gps, create_id_dict, get_distance


def sort_projects_by_news_pub_dates(projects_qs):
    return (
        projects_qs.filter(active=True)
        .filter(hidden=False)
        .annotate(
            latest_article_pub_date=Coalesce(
                Max("article__publication_date"),
                Value("1970-01-01"),
                output_field=DateTimeField(),
            )
        )
        .annotate(
            latest_warning_pub_date=Coalesce(
                Max("warningmessage__publication_date"),
                Value("1970-01-01"),
                output_field=DateTimeField(),
            )
        )
        .annotate(
            latest_pub_date=Greatest(
                "latest_article_pub_date", "latest_warning_pub_date"
            )
        )
        .order_by("-latest_pub_date")
    )


def create_project_news_lookup(projects: list[Project], article_max_age):
    """Create lookup table to quickly find articles by project id"""
    # Prefetch articles and warning messages within date range
    datetime_now = datetime.now().astimezone()
    start_date = datetime_now - timedelta(days=int(article_max_age))
    end_date = datetime_now

    # Setup lookup table
    project_news_mapping = {x.pk: [] for x in projects}

    def pre_fetch_news(model, project_id_key):
        pre_fetched_qs = model.objects.filter(
            publication_date__range=[start_date, end_date]
        ).values("id", "modification_date", project_id_key)
        pre_fetched = list(pre_fetched_qs)

        # Remap articles to lookup table with project id as key
        for obj in pre_fetched:
            # Keep in sync with ArticleMinimalSerializer
            news_dict = {
                "meta_id": create_id_dict(model, obj["id"]),
                "modification_date": str(obj["modification_date"]),
            }
            if obj[project_id_key] in [x.pk for x in projects]:
                project_news_mapping[obj[project_id_key]].append(news_dict)

    pre_fetch_news(Article, "projects")
    pre_fetch_news(WarningMessage, "project")

    return project_news_mapping


def _paginate_data(request, data: list) -> dict:
    """Create pagination of data"""
    page = int(request.GET.get("page", 1)) - 1
    page_size = int(request.GET.get("page_size", 10))

    # Get uri from request
    absolute_uri = request.build_absolute_uri()
    uri = absolute_uri.split("?")[0]

    # NOTE: check if pagination does not return double results
    # might be an index + 1 issue?
    start_index = page * page_size
    stop_index = page * page_size + page_size
    paginated_result = data[start_index:stop_index]
    pages = int(ceil(len(data) / float(page_size)))

    pagination = {
        "number": page + 1,
        "size": page_size,
        "totalElements": len(data),
        "totalPages": pages,
    }

    # Get query parameters from request
    query_params = dict(request.query_params)
    query_params.pop("page", None)
    query_params.pop("page_size", None)

    query_params_str = ""
    for k, v in query_params.items():
        param_str = f"&{k}={v[0]}"
        query_params_str += param_str

    # Add link without pagination
    links = {"self": {"href": f"{uri}?{query_params_str}"}}

    # Add next page link, if available
    if pagination["number"] < pagination["totalPages"]:
        next_page = str(pagination["number"] + 1)
        links["next"] = {
            "href": f"{uri}?page={next_page}&page_size={page_size}{query_params_str}"
        }

    # Add previous page link, if available
    if pagination["number"] > 1:
        previous_page = str(pagination["number"] - 1)
        links["previous"] = {
            "href": f"{uri}?page={previous_page}&page_size={page_size}{query_params_str}"
        }

    return {
        "result": paginated_result,
        "page": pagination,
        "_links": links,
    }


def _projects(request):
    """Get a list of all projects in specific order"""

    device_id = request.headers.get(settings.HEADER_DEVICE_ID, None)
    if device_id is None:
        return Response(
            data="Invalid header(s). See /api/v1/apidocs for more information",
            status=status.HTTP_400_BAD_REQUEST,
        )

    lat = request.GET.get("lat", None)
    lon = request.GET.get("lon", None)
    address = request.GET.get("address", None)

    # NOTE: is 3 days too little, users will miss many article updates
    article_max_age = int(
        request.GET.get(settings.ARTICLE_MAX_AGE_PARAM, 3)
    )  # Max days since publication date

    # NOTE: cache should be rebuild when any parameter is changed
    # currently only device id is used as cache key
    # @memoize
    def _fetch_projects(_device_id, _article_max_age, _lat, _lon, _address):
        # Convert address into GPS data. Note: This should never happen, the device should already
        if _address is not None and (_lat is None or _lon is None):
            _lat, _lon = address_to_gps(_address)

        device = Device.objects.filter(device_id=_device_id).first()

        # Sort followed projects by project with most recent article and warnings,
        projects_followed_by_device_qs = None
        if device:
            projects_followed_by_device_qs = sort_projects_by_news_pub_dates(
                device.followed_projects
            )
        projects_followed_by_device = list(
            projects_followed_by_device_qs if projects_followed_by_device_qs else []
        )

        def calculate_distance(project: Project, _lat, _lon):
            given_cords = (float(_lat), float(_lon))

            if project.coordinates is not None:
                project_cords = (
                    project.coordinates.get("lat"),
                    project.coordinates.get("lon"),
                )
            else:
                project_cords = (None, None)

            meter = get_distance(given_cords, project_cords)
            if meter is None:
                return float("inf")
            return meter

        # Get all projects not followed by device
        all_other_projects_qs = None
        if projects_followed_by_device_qs:
            all_other_projects_qs = (
                Project.objects.filter(active=True)
                .filter(hidden=False)
                .exclude(pk__in=projects_followed_by_device_qs)
            )
        else:
            all_other_projects_qs = (
                Project.objects.filter(active=True).filter(hidden=False).all()
            )
        # If lat and lon are known:
        # Sort remaining projects by distance from given coordinates
        if _lat is not None and _lon is not None:
            all_other_projects = sorted(
                all_other_projects_qs,
                key=lambda project: calculate_distance(project, _lat, _lon),
            )
        # If lat and lon are not known:
        # Sort projects by most recent article,
        # adding old date for projects without articles

        else:
            all_other_projects_qs = sort_projects_by_news_pub_dates(
                all_other_projects_qs
            )
            all_other_projects = list(all_other_projects_qs)

        # Combine followed and all other projects in a single list
        all_projects = []
        all_projects.extend(projects_followed_by_device)
        all_projects.extend(all_other_projects)

        project_news_mapping = create_project_news_lookup(
            all_projects, _article_max_age
        )

        context = {
            "lat": _lat,
            "lon": _lon,
            "project_news_mapping": project_news_mapping,
            "followed_projects": projects_followed_by_device,
        }
        serializer = ProjectExtendedSerializer(
            instance=all_projects, many=True, context=context
        )
        return serializer.data

    # Create context for project list serializer
    serialized_data = _fetch_projects(device_id, article_max_age, lat, lon, address)

    # Paginate and return data
    paginated_data = _paginate_data(request, serialized_data)
    return Response(
        data=paginated_data, status=status.HTTP_200_OK, content_type="application/json"
    )


class ProjectsListView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        """Get a list of all projects in specific order"""
        return _projects(request)
