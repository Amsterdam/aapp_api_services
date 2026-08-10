MOCK_RESPONSE = [
    {"id": 1, "name": "PreAuthorizationAmount", "value": "45"},
    {"id": 2, "name": "SessionCleanupEnabled", "value": "false"},
    {"id": 3, "name": "SessionExpiryHours", "value": "24"},
    {"id": 4, "name": "SessionExpiryWarningHours", "value": "2"},
    {"id": 5, "name": "StandardFine", "value": "1"},
    {"id": 6, "name": "VatFraction", "value": "1.21"},
]

MOCK_RESPONSE_MISSING_FIELDS = [
    {"id": 1, "name": "PreAuthorizationAmount", "value": "45"},
    {"id": 2, "name": "SessionCleanupEnabled", "value": "true"},
    {"id": 3, "name": "SessionExpiryHours", "value": "24"},
    # Missing SessionExpiryWarningHours and StandardFine
]
