from django.test import TestCase
from model_bakery import baker

from news.models import NewsArticle, NewsArticleImage


class NewsArticleImageModelTest(TestCase):
    def setUp(self):
        self.article = baker.make(NewsArticle)

    def test_multiple_images_can_be_added(self):
        img1 = baker.make(NewsArticleImage, article=self.article)
        img2 = baker.make(NewsArticleImage, article=self.article)

        # Check that both images are associated with the article
        images = NewsArticleImage.objects.filter(article=self.article)
        self.assertEqual(images.count(), 2)
        self.assertIn(img1, images)
        self.assertIn(img2, images)

    def test_images_are_retrievable_by_article(self):
        img1 = baker.make(NewsArticleImage, article=self.article)
        img2 = baker.make(NewsArticleImage, article=self.article)

        # Use related_name 'images' to get images from article
        images = list(self.article.images.all())
        self.assertEqual(len(images), 2)
        self.assertIn(img1, images)
        self.assertIn(img2, images)
