from contact.enums.base import ChoicesEnum, ServiceClass
from contact.icons import icon_svg
from contact.services.taps import TapService
from contact.services.toilets import ToiletService


class Services(ChoicesEnum):
    TOILET = ServiceClass(
        id=1,
        title="Openbare toiletten",
        icon=icon_svg("toilet"),
        dataservice=ToiletService,
    )
    TAP = ServiceClass(
        id=2, title="Drinkwater", icon=icon_svg("tap"), dataservice=TapService
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
