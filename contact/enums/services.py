from contact.enums.base import ChoicesEnum, ServiceClass
from contact.services.taps import TapService
from contact.icons import IconPath
from contact.services.toilets import ToiletService


class Services(ChoicesEnum):
    TOILET = ServiceClass(
        id=1,
        title="Openbare toiletten",
        icon=IconPath.get("toilet"),
        dataservice=ToiletService,
    )
    TAP = ServiceClass(
        id=2, title="Drinkwater", icon=IconPath.get("tap"), dataservice=TapService
    )

    @classmethod
    def get_service_by_id(cls, id: int) -> ServiceClass | None:
        """
        Return the service class for the given id, or None if not found.
        """
        for item in cls:
            if item.value.id == id:
                return item.value
        return None
