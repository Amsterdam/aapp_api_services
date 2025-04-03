import hashlib
from collections import defaultdict

from rest_framework import serializers

SERIALIZERS = {}


def get_error_response_serializers(exceptions):
    exceptions_per_status = defaultdict(list)
    for exception in exceptions or []:
        exceptions_per_status[exception.status_code].append(exception)

    error_response_serializers = {}
    for status_code, exceptions in exceptions_per_status.items():
        serializer = get_serializer(status_code=status_code, exceptions=exceptions)
        error_response_serializers[status_code] = serializer
    return error_response_serializers


def get_serializer(status_code, exceptions):
    for exp in exceptions:
        assert status_code == exp.status_code, (
            "All exceptions must have the same status code"
        )

    hash_val = get_hash(exceptions)
    if hash_val in SERIALIZERS:
        return SERIALIZERS[hash_val]

    serializer = create_serializer(
        status_code=status_code, exceptions=exceptions, hash_val=hash_val
    )
    SERIALIZERS[hash_val] = serializer
    return serializer


def create_serializer(status_code, exceptions, hash_val):
    hash_val = get_hash(exceptions)

    class ExceptionSerializer(serializers.Serializer):
        class Meta:
            ref_name = (
                f"Status{status_code}_{hash_val}Serializer"  # Unique serializer name
            )

        code = serializers.ChoiceField(
            choices=[(exp.default_code, exp.default_detail) for exp in exceptions]
        )
        detail = serializers.CharField(default=exceptions[0].default_detail)

    return ExceptionSerializer


def get_hash(exceptions):
    exp_names = [exception.default_code for exception in exceptions]
    exp_names.sort()
    combined_string = "".join(exp_names)
    hash_val = hashlib.sha256(combined_string.encode()).hexdigest()
    return hash_val[:8]  # Shorten hash for readability
