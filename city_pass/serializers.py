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
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    initials = serializers.CharField()
    infix = serializers.CharField(required=False)


class MijnAmsPassBudgetSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
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

class MijnAmsPassBudgetTransactionsSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    amount = serializers.FloatField()
    amountFormatted = serializers.CharField()
    datePublished = serializers.CharField()
    datePublishedFormatted = serializers.CharField()
    budget = serializers.CharField()
    budgetCode = serializers.CharField()