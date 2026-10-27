from django.test import SimpleTestCase

from construction_work.models.article_models import ArticleImage
from construction_work.models.project_models import ProjectImage
from construction_work.serializers.general_serializers import serialize_image_variants


class ImageSerializationTests(SimpleTestCase):
    def test_empty_variants_have_no_image(self):
        self.assertIsNone(serialize_image_variants([]))

    def test_simplified_models_keep_the_image_response_shape(self):
        for model in (ArticleImage, ProjectImage):
            with self.subTest(model=model):
                variants = [
                    model(
                        id=999,
                        foreign_id=123,
                        uri="https://example.com/image.jpg",
                        width=200,
                        height=100,
                    ),
                    model(
                        foreign_id=123,
                        uri="https://example.com/image-small.jpg",
                        width=100,
                        height=50,
                    ),
                ]
                self.assertEqual(
                    serialize_image_variants(variants),
                    {
                        "id": 123,
                        "image_set": 123,
                        "aspectRatio": 2.0,
                        "alternativeText": None,
                        "sources": [
                            {
                                "uri": variant.uri,
                                "width": variant.width,
                                "height": variant.height,
                            }
                            for variant in variants
                        ],
                    },
                )

    def test_zero_height_has_no_aspect_ratio(self):
        variant = ArticleImage(foreign_id=123, width=100, height=0)
        self.assertIsNone(serialize_image_variants([variant])["aspectRatio"])
