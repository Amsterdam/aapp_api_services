from construction_work.models.article_models import Article, ArticleImage
from construction_work.models.manage_models import Device
from construction_work.services.notification import ArticleNotificationService
from core.services.notification_service import (
    NotificationData,
)


def send_article_notifications(
    current_drupal_ids: list[int], found_drupal_ids: list[int]
):
    notification_service = ArticleNotificationService(use_image_service=True)
    new_article_ids = get_new_articles(
        current_drupal_ids=current_drupal_ids, found_drupal_ids=found_drupal_ids
    )

    for new_article_id in new_article_ids:
        new_article = Article.objects.filter(drupal_id=new_article_id).first()
        projects = new_article.projects.all()

        # get image of article
        article_image = ArticleImage.objects.filter(article_id=new_article.id).first()
        if article_image:
            image_set_id = article_image.foreign_id
        else:
            image_set_id = None

        for project in projects:
            device_ids = list(
                Device.objects.filter(followed_projects__id=project.id).values_list(
                    "device_id", flat=True
                )
            )
            if len(device_ids) > 0:
                notification_data = NotificationData(
                    title=project.title,
                    message=new_article.title,
                    link_source_id=str(new_article.pk),
                    device_ids=device_ids,
                    image_set_id=image_set_id,
                )

                notification_service.send(notification_data)


def get_new_articles(
    current_drupal_ids: list[int], found_drupal_ids: list[int]
) -> list[int]:
    new_articles_foreign_ids = []
    for found_article_id in found_drupal_ids:
        if found_article_id not in current_drupal_ids:
            new_articles_foreign_ids.append(found_article_id)

    return new_articles_foreign_ids
