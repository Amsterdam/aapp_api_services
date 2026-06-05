from .base import ChoicesEnum, NewsArticleExtract


class NewsArticleSource(ChoicesEnum):
    """
    Enum class representing the different sources of news articles.
    Each source is associated with a NewsArticleExtract instance,
    which contains the index, type, and district information for that source.

    !! IMPORTANT: overlap is preserved via source flags, but the order still matters
    for the legacy `type` field, which keeps overwrite behavior for backward compatibility. !!
    """

    ALL_NEWS = NewsArticleExtract(
        index="all_news", type="article", boolean_column="in_all_news", district=None
    )
    HIGHLIGHT = NewsArticleExtract(
        index="highlighted",
        type="highlight",
        boolean_column="is_highlight",
        district=None,
    )
    LIVEBLOG = NewsArticleExtract(
        index="liveblogs", type="liveblog", boolean_column="is_liveblog", district=None
    )
    DISTRICT_NOORD = NewsArticleExtract(
        index="nieuws-stadsdeel-noord",
        type="district",
        boolean_column="is_district",
        district="noord",
    )
    DISTRICT_WEST = NewsArticleExtract(
        index="nieuws-stadsdeel-west",
        type="district",
        boolean_column="is_district",
        district="west",
    )
    DISTRICT_ZUID = NewsArticleExtract(
        index="nieuws-stadsdeel-zuid",
        type="district",
        boolean_column="is_district",
        district="zuid",
    )
    DISTRICT_OOST = NewsArticleExtract(
        index="nieuws-stadsdeel-nieuw-oost",
        type="district",
        boolean_column="is_district",
        district="oost",
    )
    DISTRICT_CENTRUM = NewsArticleExtract(
        index="nieuws-stadsdeel-centrum",
        type="district",
        boolean_column="is_district",
        district="centrum",
    )
    DISTRICT_NIEUW_WEST = NewsArticleExtract(
        index="nieuws-stadsdeel-nieuw-west",
        type="district",
        boolean_column="is_district",
        district="nieuw-west",
    )
    DISTRICT_ZUIDOOST = NewsArticleExtract(
        index="nieuws-stadsdeel-zuidoost",
        type="district",
        boolean_column="is_district",
        district="zuidoost",
    )
    DISTRICT_WEESP = NewsArticleExtract(
        index="nieuws-stadgebied-weesp",
        type="district",
        boolean_column="is_district",
        district="weesp",
    )
