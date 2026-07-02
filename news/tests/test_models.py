from django.db import IntegrityError
from django.test import TestCase
from model_bakery import baker

from news.models.article_models import NewsArticle, NewsArticleImage


class NewsArticleImageModelTest(TestCase):
    def setUp(self):
        self.article = baker.make(NewsArticle, in_all_news=True)

    def test_multiple_images_can_be_added(self):
        img1 = baker.make(NewsArticleImage, parent=self.article)
        img2 = baker.make(NewsArticleImage, parent=self.article)

        # Check that both images are associated with the article
        images = NewsArticleImage.objects.filter(parent=self.article)
        self.assertEqual(images.count(), 2)
        self.assertIn(img1, images)
        self.assertIn(img2, images)

    def test_images_are_retrievable_by_article(self):
        img1 = baker.make(NewsArticleImage, parent=self.article)
        img2 = baker.make(NewsArticleImage, parent=self.article)

        # Use related_name 'images' to get images from article
        images = list(self.article.images.all())
        self.assertEqual(len(images), 2)
        self.assertIn(img1, images)
        self.assertIn(img2, images)

    def test_district_article_should_contain_district(self):
        article = baker.make(NewsArticle, is_district=True, district="noord")
        self.assertEqual(article.district, "noord")

    def test_district_article_without_district_should_fail(self):
        with self.assertRaises(IntegrityError):
            baker.make(NewsArticle, is_district=True, district=None)
