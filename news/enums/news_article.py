from .base import ChoicesEnum, NewsArticleExtract


class NewsArticleSource(ChoicesEnum):
    """
    Enum class representing the different sources of news articles.
    Each source is associated with a NewsArticleExtract instance,
    which contains the index, boolean_column, and district information for that source.
    """

    ALL_NEWS = NewsArticleExtract(
        tag_id=531, boolean_column="in_all_news", district=None
    )
    HIGHLIGHT = NewsArticleExtract(
        tag_id=491,
        boolean_column="is_highlight",
        district=None,
    )
    ACTIVE_LIVEBLOG = NewsArticleExtract(
        tag_id=2696, boolean_column="is_active_liveblog", district=None
    )
    DISTRICT_NOORD = NewsArticleExtract(
        tag_id=779,
        boolean_column="is_district",
        district="noord",
    )
    DISTRICT_WEST = NewsArticleExtract(
        tag_id=781,
        boolean_column="is_district",
        district="west",
    )
    DISTRICT_ZUID = NewsArticleExtract(
        tag_id=782,
        boolean_column="is_district",
        district="zuid",
    )
    DISTRICT_OOST = NewsArticleExtract(
        tag_id=780,
        boolean_column="is_district",
        district="oost",
    )
    DISTRICT_CENTRUM = NewsArticleExtract(
        tag_id=777,
        boolean_column="is_district",
        district="centrum",
    )
    DISTRICT_NIEUW_WEST = NewsArticleExtract(
        tag_id=778,
        boolean_column="is_district",
        district="nieuw-west",
    )
    DISTRICT_ZUIDOOST = NewsArticleExtract(
        tag_id=783,
        boolean_column="is_district",
        district="zuidoost",
    )
    DISTRICT_WEESP = NewsArticleExtract(
        tag_id=814,
        boolean_column="is_district",
        district="weesp",
    )
