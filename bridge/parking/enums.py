from enum import Enum


class NotificationStatus(Enum):
    ERROR = "Error occurred while processing reminder"
    CREATED = "Reminder has been created"
    CANCELLED = "Reminder has been cancelled"
    NO_ACTION = "No action taken for reminder"
