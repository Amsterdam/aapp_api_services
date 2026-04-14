from contact.enums.base import ChoicesEnum, ModuleSourceChoices, ServiceClass
from contact.icons import IconPath
from contact.services.taps import TapService
from contact.services.toilets import ToiletService


class Services(ChoicesEnum):
    SERVICES_TOILET = ServiceClass(
        id=1,
        title="Openbare toiletten",
        icon=IconPath.get("toilet"),
        dataservice=ToiletService,
        input_module=ModuleSourceChoices.HANDIG_IN_DE_STAD.value,
    )
    SERVICES_TAP = ServiceClass(
        id=2,
        title="Drinkwater",
        icon=IconPath.get("tap"),
        dataservice=TapService,
        input_module=ModuleSourceChoices.HANDIG_IN_DE_STAD.value,
    )
    KINGSDAY_LAND = ServiceClass(
        id=3,
        title="Ter land",
        icon=IconPath.get("info"),
        dataservice=None,
        input_module=ModuleSourceChoices.KONINGSDAG.value,
    )
    KINGSDAY_WATER = ServiceClass(
        id=4,
        title="Te water",
        icon=IconPath.get("info"),
        dataservice=None,
        input_module=ModuleSourceChoices.KONINGSDAG.value,
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
