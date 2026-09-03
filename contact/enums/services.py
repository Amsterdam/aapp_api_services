from contact.enums.base import ChoicesEnum, ModuleSourceChoices, ServiceClass
from contact.icons import IconPath
from contact.services.christmas_tree import ChristmasTreeService
from contact.services.kingsday_land import KingsdayLandService
from contact.services.kingsday_water import KingsdayWaterService
from contact.services.pride_map import PrideMapService
from contact.services.swimming_spots import SwimmingSpotService
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
        title="Op straat",
        icon=IconPath.get("kingsday-land"),
        dataservice=KingsdayLandService,
        input_module=ModuleSourceChoices.KONINGSDAG.value,
    )
    KINGSDAY_WATER = ServiceClass(
        id=4,
        title="Op het water",
        icon=IconPath.get("kingsday-water"),
        dataservice=KingsdayWaterService,
        input_module=ModuleSourceChoices.KONINGSDAG.value,
    )
    SWIMMING_SPOTS = ServiceClass(
        id=5,
        title="Zwemplekken",
        icon=IconPath.get("swimming-spots"),
        dataservice=SwimmingSpotService,
        input_module=ModuleSourceChoices.HANDIG_IN_DE_STAD.value,
    )
    PRIDE_MAP = ServiceClass(
        id=6,
        title="Kaart",
        icon=IconPath.get("pride-map"),
        dataservice=PrideMapService,
        input_module=ModuleSourceChoices.PRIDE.value,
    )
    CHRISTMAS_TREES = ServiceClass(
        id=7,
        title="Kerstbomen",
        icon=IconPath.get("christmas-tree"),
        dataservice=ChristmasTreeService,
        input_module=ModuleSourceChoices.WASTE.value,
        is_active=False,  # this service should currently not show up when all services are requested
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
