from enum import Enum


class NotificationStatus(Enum):
    NO_CHANGE = "Reminders have not been changed"
    ERROR = "Error occurred while processing reminder"
    CREATED = "Reminder has been created"
    UPDATED = "Reminder has been updated"
    CANCELLED = "Reminder has been cancelled"
