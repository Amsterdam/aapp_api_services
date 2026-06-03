from .base import ChoicesEnum, NewsArticleExtract


class NewsArticleSource(ChoicesEnum):
    """
    Enum class representing the different sources of news articles.
    Each source is associated with a NewsArticleExtract instance,
    which contains the index, type, and district information for that source.

    !! IMPORTANT: the order matters! The types of the sources are used to determine
    how to store the article in the database, where the type is overwritten by the
    type of the source if there are duplicates. For example, if an article is retrieved
    from both the "all_news" and "liveblogs" sources, it should be stored as a "liveblog"
    in the database, because the "liveblogs" source has a higher priority than the "all_news"
    source. !!
    """

    ALL_NEWS = NewsArticleExtract(index="all_news", type="article", district=None)
    HIGHLIGHT = NewsArticleExtract(index="highlighted", type="highlight", district=None)
    LIVEBLOG = NewsArticleExtract(index="liveblogs", type="liveblog", district=None)
    DISTRICT_NOORD = NewsArticleExtract(
        index="nieuws-stadsdeel-noord", type="district", district="noord"
    )
    DISTRICT_WEST = NewsArticleExtract(
        index="nieuws-stadsdeel-west", type="district", district="west"
    )
    DISTRICT_ZUID = NewsArticleExtract(
        index="nieuws-stadsdeel-zuid", type="district", district="zuid"
    )
    DISTRICT_OOST = NewsArticleExtract(
        index="nieuws-stadsdeel-nieuw-oost", type="district", district="oost"
    )
    DISTRICT_CENTRUM = NewsArticleExtract(
        index="nieuws-stadsdeel-centrum", type="district", district="centrum"
    )
    DISTRICT_NIEUW_WEST = NewsArticleExtract(
        index="nieuws-stadsdeel-nieuw-west", type="district", district="nieuw-west"
    )
    DISTRICT_ZUIDOOST = NewsArticleExtract(
        index="nieuws-stadsdeel-zuidoost", type="district", district="zuidoost"
    )
    DISTRICT_WEESP = NewsArticleExtract(
        index="nieuws-stadgebied-weesp", type="district", district="weesp"
    )
