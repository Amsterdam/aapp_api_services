from rest_framework import serializers


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
    securityCode = serializers.CharField(allow_null=True)


class MijnAmsPassBudgetTransactionsSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    amount = serializers.FloatField()
    amountFormatted = serializers.CharField()
    datePublished = serializers.CharField()
    datePublishedFormatted = serializers.CharField()
    budget = serializers.CharField()
    budgetCode = serializers.CharField()


class MijnAmsPassAanbiedingTransactionsSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField(allow_null=True)
    description = serializers.CharField()
    discountTitle = serializers.CharField()
    discountAmount = serializers.FloatField()
    discountAmountFormatted = serializers.CharField()
    datePublished = serializers.CharField()
    datePublishedFormatted = serializers.CharField()


class MijnAmsPassAanbiedingSerializer(serializers.Serializer):
    discountAmountTotal = serializers.FloatField()
    discountAmountTotalFormatted = serializers.CharField()
    transactions = MijnAmsPassAanbiedingTransactionsSerializer(many=True)
