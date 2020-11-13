from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    def __str__(self):
        return self.username


class Field(models.Model):
    STRING = "string"
    DATE = "date"
    FIELD_TYPE = ((STRING, "string"), (DATE, "date"))

    field_type = models.CharField(choices=FIELD_TYPE, max_length=255)
    field_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)


class FieldValue(models.Model):

    date_value = models.DateTimeField(null=True)
    string_value = models.TextField(null=True)
    field = models.ForeignKey(Field, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)


class Trigger(models.Model):

    PERIOD = (
        ("am", "am"),
        ("pm", "pm"),
    )

    OFFSET_TYPE = (
        ("on_days", "on_days"),
        ("days_before", "days_before"),
        ("days_after", "days_after"),
    )

    field = models.ForeignKey(Field, on_delete=models.DO_NOTHING)
    time = models.TimeField()
    period = models.CharField(choices=PERIOD, max_length=2)
    offset_type = models.CharField(choices=OFFSET_TYPE, max_length=255)
    date_offset = models.PositiveSmallIntegerField(default=0)


class ScheduleView(models.Model):

    timestamp = models.PositiveIntegerField()
    trigger_id = models.CharField(max_length=255)
    fieldvalue_id = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["trigger_id"]),
            models.Index(fields=["fieldvalue_id"]),
        ]
