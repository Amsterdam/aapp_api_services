from .base import ChoicesEnum, NewsArticleExtract


class NewsArticleSource(ChoicesEnum):
    HIGHLIGHT = NewsArticleExtract(index="highlighted", type="highlight", district=None)
    LIVEBLOG = NewsArticleExtract(index="liveblogs", type="liveblog", district=None)
    DISTRICT_NOORD = NewsArticleExtract(
        index="nieuws-stadsdeel-noord", type="district", district="noord"
    )
    DISTRICT_ZUID = NewsArticleExtract(
        index="nieuws-stadsdeel-zuid", type="district", district="zuid"
    )
    ALL_NEWS = NewsArticleExtract(index="all_news", type="article", district=None)
