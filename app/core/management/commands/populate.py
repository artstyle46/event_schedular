from django.core.management import BaseCommand

from django.contrib.auth import get_user_model
from core.models import Field, FieldValue, Trigger
import random
from datetime import datetime, timedelta


def create_user():
    user_list = []
    for i in range(10000):
        user_list.append(
            get_user_model().objects.create(username=f"asit_{i}", password="test")
        )
    return user_list


class Command(BaseCommand):
    def handle(self, *args, **options):

        user_list = create_user()
        field_list = []
        field_type = ["date", "string"]
        for i in range(100):
            choice = random.choice(field_type)
            f1 = Field(field_type=choice, field_name=f"choice_{i}")
            f1.save()
            field_list.append(f1)

        for i in range(2000000):
            rand_user = random.randrange(0, 9999)
            u = user_list[rand_user]
            rand_field = random.randrange(0, 99)
            field = field_list[rand_field]
            field_data = []
            if field.field_type == "date":
                rand_hour = random.randrange(0, 23)
                rand_minute = random.randrange(0, 59)
                today = datetime.now().date()
                if i > 1000000:
                    today = datetime.now().date() + timedelta(days=1)
                random_date = datetime(
                    today.year, today.month, today.day, rand_hour, rand_minute
                )
                field_value = FieldValue(field=field, date_value=random_date, user=u)
                field_data.append(field_value)
            else:
                field_value = FieldValue(
                    field=field, string_value=f"string_{i}", user=u
                )
                field_data.append(field_value)
        FieldValue.objects.bulk_create(field_data)

        date_fields = Field.objects.filter(field_type="date")[20:]
        date_len = len(date_fields)
        for i in range(date_len):
            if len(date_fields) == 0:
                break
            rand_hour = random.randrange(0, 11)
            rand_minute = random.randrange(0, 59)
            period = random.choice(["am", "pm"])
            offset_type = random.choice(["on_days", "days_before", "days_after"])
            date_offset = 0
            if offset_type != "on_days":
                date_offset = random.randrange(0, 5)
            trigger = Trigger(
                field=date_fields[i],
                time=f"{rand_hour}:{rand_minute}",
                period=period,
                offset_type=offset_type,
                date_offset=date_offset,
            )
            trigger.save()
