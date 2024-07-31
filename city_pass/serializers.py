from rest_framework import serializers


class DetailResultSerializer(serializers.Serializer):
    detail = serializers.CharField()


class SessionTokensOutSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class SessionCredentialInSerializer(serializers.Serializer):
    session_token = serializers.CharField(required=True)
    encrypted_administration_no = serializers.CharField(required=True)


class SessionRefreshInSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)


class MijnAmsPassOwnerSerializer(serializers.Serializer):
    initials = serializers.CharField()
    firstname = serializers.CharField()
    infix = serializers.CharField()
    lastname = serializers.CharField()


class MijnAmsPassBudgetSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    code = serializers.CharField()
    budgetAssigned = serializers.FloatField()
    budgetAssignedFormatted = serializers.CharField()
    budgetBalance = serializers.FloatField()
    budgetBalanceFormatted = serializers.CharField()
    dateEnd = serializers.CharField()
    dateEndFormatted = serializers.CharField()


class MijnAmsPassDataSerializer(serializers.Serializer):
    id = serializers.CharField()
    passNumber = serializers.IntegerField()
    passNumberComplete = serializers.CharField()
    owner = MijnAmsPassOwnerSerializer()
    dateEnd = serializers.CharField()
    dateEndFormatted = serializers.CharField()
    budgets = MijnAmsPassBudgetSerializer(many=True)
    balanceFormatted = serializers.CharField()
