from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from construction_work.etl.send_notifications import send_article_notifications
from construction_work.models.article_models import Article
from construction_work.models.manage_models import Device
from construction_work.models.project_models import Project
from core.services.notification_service import ScheduledNotification


class SendNotificationTestCase(TestCase):
    databases = {"default", "notification"}

    def setUp(self):
        # Create some test projects and articles
        self.project1 = Project.objects.create(
            foreign_id=1,
            title="Project 1",
            active=True,
            hidden=False,
            last_seen=timezone.now(),
        )
        self.article1 = baker.make(
            Article,
            foreign_id=1,
            title="Article 1",
            last_seen=timezone.now(),
            projects=[self.project1],
        )
        baker.make(Device, device_id="test_id", followed_projects=[self.project1])

    def test_send_notification(self):
        current_article_ids = set(Article.objects.values_list("foreign_id", flat=True))
        self.article2 = baker.make(
            Article,
            foreign_id=2,
            title="Article 2",
            last_seen=timezone.now(),
            projects=[self.project1],
        )
        found_articles = [1, 2]  # Two articles are found

        send_article_notifications(
            current_foreign_ids=current_article_ids, found_articles=found_articles
        )

        notifications = ScheduledNotification.objects.all()

        self.assertEqual(
            notifications.count(), 1
        )  # one notification is added (for article 2)
        self.assertEqual(notifications[0].title, self.project1.title)
        self.assertEqual(notifications[0].body, self.article2.title)
