from rest_framework import serializers


class NotRequiredBlankToNullCharField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = False
        self.allow_null = True
        self.allow_blank = True

    def to_representation(self, value):
        if value == "":
            return None
        return super().to_representation(value)


class MijnAmsPassOwnerSerializer(serializers.Serializer):
    firstname = NotRequiredBlankToNullCharField()
    lastname = serializers.CharField()
    initials = NotRequiredBlankToNullCharField()
    infix = NotRequiredBlankToNullCharField()


class MijnAmsPassBudgetSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = NotRequiredBlankToNullCharField()
    code = serializers.CharField()
    budgetAssigned = serializers.FloatField(required=False)
    budgetAssignedFormatted = serializers.CharField()
    budgetBalance = serializers.FloatField(required=False)
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
    actief = serializers.BooleanField()
    securityCode = NotRequiredBlankToNullCharField()


class MijnAmsPassBudgetTransactionsSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    amount = serializers.FloatField(required=False)
    amountFormatted = serializers.CharField()
    datePublished = serializers.CharField()
    datePublishedFormatted = serializers.CharField()
    budget = serializers.CharField()
    budgetCode = serializers.CharField()


class MijnAmsPassAanbiedingTransactionsSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = NotRequiredBlankToNullCharField()
    description = serializers.CharField()
    discountTitle = serializers.CharField()
    discountAmount = serializers.FloatField(required=False)
    discountAmountFormatted = serializers.CharField()
    datePublished = serializers.CharField()
    datePublishedFormatted = serializers.CharField()


class MijnAmsPassAanbiedingSerializer(serializers.Serializer):
    discountAmountTotal = serializers.FloatField(required=False)
    discountAmountTotalFormatted = serializers.CharField()
    transactions = MijnAmsPassAanbiedingTransactionsSerializer(many=True)


class MijnAmsPassBlockSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["BLOCKED"])
