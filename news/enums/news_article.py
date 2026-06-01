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
    DISTRICT_ZUID = NewsArticleExtract(
        index="nieuws-stadsdeel-zuid", type="district", district="zuid"
    )
