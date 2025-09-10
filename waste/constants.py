from enum import Enum


class District(Enum):
    CENTRUM = "Centrum"
    NIEUW_WEST = "Nieuw-West"
    NOORD = "Noord"
    OOST = "Oost"
    WEST = "West"
    ZUID = "Zuid"
    ZUIDOOST = "Zuidoost"
    WEESP = "Weesp"
    WESTPOORT = "Westpoort"


DISTRICT_POSTAL_CODE_MAPPING = {
    District.CENTRUM: [("1011", "1018")],
    District.NOORD: [("1020", "1039")],
    District.OOST: [("1019", "1019"), ("1086", "1099")],
    District.WESTPOORT: [("1040", "1049")],
    District.WEST: [("1050", "1059")],
    District.NIEUW_WEST: [("1060", "1069")],
    District.ZUID: [("1070", "1083")],
    District.ZUIDOOST: [("1100", "1108")],
    District.WEESP: [("1380", "1384")],
}

DISTRICT_PASS_NUMBER_MAPPING = {
    District.CENTRUM: "80706D8A189404",
    District.NIEUW_WEST: "80706D8A2E9504",
    District.NOORD: "80706D8A3F8604",
    District.OOST: "80706D8A4B9304",
    District.WEST: "80706D8A72BD04",
    District.ZUID: "80706DAA58604",
    District.ZUIDOOST: "80706D8AAD9604",
    District.WEESP: "80706D8AD88404",
    District.WESTPOORT: "80706D8A897004",
}

# Postal codes ranges where container is not present
# - Items in list are areas where container is not present
# - Empty list means no containers are present in entire code range
POSTAL_CODE_CONTAINER_NOT_PRESENT = {
    ("1011", "1011"): ["AB"],
    ("1020", "1020"): ["AB"],
    ("1019", "1100"): [],
}

WASTE_TYPES_ORDER = ["Rest", "GA", "Papier", "GFT", "Glas", "Textiel"]

WASTE_COLLECTION_BY_APPOINTMENT_CODE = "THUISAFSPR"

WASTE_TYPES_INACTIVE = ["Plastic"]
