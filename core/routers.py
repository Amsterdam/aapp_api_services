from django.conf import settings


class NotificationRouter:
    notification_app_labels = {"notification"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.notification_app_labels:
            return "notification"
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.notification_app_labels:
            return "notification"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.notification_app_labels
            or obj2._meta.app_label in self.notification_app_labels
        ):
            return obj1._state.db == obj2._state.db
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.notification_app_labels:
            return db == "notification" and settings.ALLOW_NOTIFICATION_DB_MIGRATE
        return db == "default"
