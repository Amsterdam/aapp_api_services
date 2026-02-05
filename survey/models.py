from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import ManyToManyField

from survey.named_tuples import (
    ConditionType,
    Orientation,
    QuestionType,
    TeamCode,
)


class Survey(models.Model):
    class Meta:
        verbose_name = "Vragenlijst"
        verbose_name_plural = "Vragenlijsten"

    title = models.CharField("Titel", max_length=200, unique=True)
    description = models.TextField("Beschrijving", max_length=1000)
    unique_code = models.CharField("Unieke code", max_length=100, unique=True)
    team = models.CharField("Team", choices=TeamCode)

    def __str__(self):
        return self.title


class SurveyConfiguration(models.Model):
    class Meta:
        verbose_name = "Vragenlijst configuratie"
        verbose_name_plural = "Vragenlijst configuraties"

    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="configuration"
    )
    location = models.CharField("Locatie", max_length=200, unique=True)
    fraction = models.FloatField(
        "Fractie",
        default=1.0,
        help_text="Hoeveel procent van de gebruikers moet deze vragenlijst krijgen?",
    )
    cooldown = models.IntegerField(
        "Cooldown",
        default=0,
        help_text="Aantal dagen voordat een gebruiker deze vragenlijst opnieuw aangeboden kan krijgen. 0 = geen cooldown.",
    )
    minimum_actions = models.IntegerField(
        "Minimaal aantal acties",
        default=0,
        help_text="Minimaal aantal acties dat een gebruiker moet hebben uitgevoerd voordat deze vragenlijst wordt aangeboden.",
    )

    def clean(self):
        super().clean()
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).values("location").first()
            if old and self.location != old["location"]:
                raise ValidationError({"location": "Cannot change once set."})

    def __str__(self):
        return f"{self.location}: {self.survey.title}"


class SurveyVersion(models.Model):
    class Meta:
        unique_together = ("survey", "version")
        ordering = ["-version"]
        verbose_name = "Vragenlijst versie"
        verbose_name_plural = "Vragenlijst versies"

    version = models.PositiveIntegerField("Versie")
    survey = models.ForeignKey(
        Survey,
        verbose_name="Vragenlijst",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField("Aangemaakt op", auto_now_add=True)
    active_from = models.DateTimeField("Actief vanaf", null=True)

    def __str__(self):
        return f"{self.survey.title} - {self.version}"


class SurveyVersionQuestion(models.Model):
    class Meta:
        unique_together = ("survey_version", "question")
        ordering = ["sort_order"]
        verbose_name = "Vragenlijst vraag"
        verbose_name_plural = "Vragenlijst vragen"

    survey_version = models.ForeignKey(SurveyVersion, on_delete=models.PROTECT)
    question = models.ForeignKey("Question", on_delete=models.PROTECT)
    sort_order = models.PositiveIntegerField(null=True)


class Question(models.Model):
    class Meta:
        verbose_name = "Vraag"
        verbose_name_plural = "Vragen"

    survey_versions = ManyToManyField(
        through=SurveyVersionQuestion,
        to=SurveyVersion,
        related_name="questions",
        verbose_name="Vragenlijst versies",
    )
    question_text = models.CharField()
    description = models.TextField(null=True, blank=True)
    question_type = models.CharField(choices=QuestionType, max_length=20)
    required = models.BooleanField()
    conditions_type = models.CharField(
        choices=(("and", "and"), ("or", "or")), default="and", max_length=3
    )
    default = models.CharField(
        max_length=100, null=True, blank=True, default="Open antwoord"
    )
    orientation = models.CharField(choices=Orientation, max_length=20)
    min_characters = models.IntegerField(default=10)
    max_characters = models.IntegerField(default=500)
    textarea_rows = models.IntegerField(default=4)

    def __str__(self):
        return f"Vraag {self.id}: {self.question_text}"


class Condition(models.Model):
    class Meta:
        unique_together = ("question", "reference_question", "value")
        verbose_name = "Conditie"
        verbose_name_plural = "Condities"

    value = models.CharField(max_length=100)
    type = models.CharField(choices=ConditionType, max_length=20)
    question = models.ForeignKey(
        Question, on_delete=models.PROTECT, related_name="conditions"
    )
    reference_question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="reference_question",
    )

    def __str__(self):
        return f"Conditie: {self.question_id}_{self.value}"


class Choice(models.Model):
    class Meta:
        ordering = ["sort_order"]
        verbose_name = "Keuze"
        verbose_name_plural = "Keuzes"

    text = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    show_textfield = models.BooleanField(default=False)
    question = models.ForeignKey(
        Question, on_delete=models.PROTECT, related_name="choices"
    )
    sort_order = models.PositiveIntegerField()

    def __str__(self):
        return f"Keuze: {self.id}"


class SurveyVersionEntry(models.Model):
    class Meta:
        verbose_name = "Ingevulde vragenlijst"
        verbose_name_plural = "Ingevulde vragenlijsten"

    survey_version = models.ForeignKey(SurveyVersion, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    entry_point = models.CharField(max_length=1000)
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"Vragenlijst: {self.survey_version.survey.title} - {self.survey_version.version}"


class Answer(models.Model):
    class Meta:
        verbose_name = "Antwoord"
        verbose_name_plural = "Antwoorden"

    survey_version_entry = models.ForeignKey(
        SurveyVersionEntry, on_delete=models.PROTECT, related_name="answers"
    )
    question = models.ForeignKey(Question, null=True, on_delete=models.PROTECT)
    answer = models.CharField(max_length=1000)

    def __str__(self):
        return f"{self.question.question_text}"
