from .base import ChoicesEnum, NewsArticleExtract


class NewsArticleSource(ChoicesEnum):
    """
    Enum class representing the different sources of news articles.
    Each source is associated with a NewsArticleExtract instance,
    which contains the index, boolean_column, and district information for that source.
    """

    ALL_NEWS = NewsArticleExtract(
        index="all_news", boolean_column="in_all_news", district=None
    )
    HIGHLIGHT = NewsArticleExtract(
        index="highlighted",
        boolean_column="is_highlight",
        district=None,
    )
    LIVEBLOG = NewsArticleExtract(
        index="liveblogs", boolean_column="is_liveblog", district=None
    )
    DISTRICT_NOORD = NewsArticleExtract(
        index="nieuws-stadsdeel-noord",
        boolean_column="is_district",
        district="noord",
    )
    DISTRICT_WEST = NewsArticleExtract(
        index="nieuws-stadsdeel-west",
        boolean_column="is_district",
        district="west",
    )
    DISTRICT_ZUID = NewsArticleExtract(
        index="nieuws-stadsdeel-zuid",
        boolean_column="is_district",
        district="zuid",
    )
    DISTRICT_OOST = NewsArticleExtract(
        index="nieuws-stadsdeel-oost",
        boolean_column="is_district",
        district="oost",
    )
    DISTRICT_CENTRUM = NewsArticleExtract(
        index="nieuws-stadsdeel-centrum",
        boolean_column="is_district",
        district="centrum",
    )
    DISTRICT_NIEUW_WEST = NewsArticleExtract(
        index="nieuws-stadsdeel-nieuw-west",
        boolean_column="is_district",
        district="nieuw-west",
    )
    DISTRICT_ZUIDOOST = NewsArticleExtract(
        index="nieuws-stadsdeel-zuidoost",
        boolean_column="is_district",
        district="zuidoost",
    )
    DISTRICT_WEESP = NewsArticleExtract(
        index="nieuws-stadgebied-weesp",
        boolean_column="is_district",
        district="weesp",
    )
