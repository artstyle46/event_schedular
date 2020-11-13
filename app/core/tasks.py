from celery import shared_task
from .models import FieldValue, Trigger, ScheduleView
import time
from datetime import datetime, timedelta


def parse_trigger_time(t, period):
    offset = 0
    if period == "pm":
        offset = 12
    hours, minutes, _ = str(t).split(":")
    hours = int(hours) + offset
    minutes = int(minutes)
    return hours, minutes


def get_timestamp(
    value_date, trigger_offset_type, trigger_date_offset, trigger_time, trigger_period
):
    hours, minutes = parse_trigger_time(trigger_time, trigger_period)
    if trigger_offset_type == "on_days":
        new_date = value_date + timedelta(hours=hours, minutes=minutes)
    elif trigger_offset_type == "days_before":
        new_date = (
            value_date
            + timedelta(hours=hours, minutes=minutes)
            - timedelta(days=trigger_date_offset)
        )
    elif trigger_offset_type == "days_after":
        new_date = (
            value_date
            + timedelta(hours=hours, minutes=minutes)
            + timedelta(days=trigger_date_offset)
        )
    return new_date.timestamp()


@shared_task(name="add_data_to_db")
def add_data_to_db():
    start_time = time.time()
    triggers = Trigger.objects.all()
    field_ids = [t.field_id for t in triggers]
    count = 0
    cur_time = datetime.now()
    valid_max_timestamp = (
        datetime(cur_time.year, cur_time.month, cur_time.day, 0, 0) + timedelta(days=1)
    ).timestamp()
    valid_min_timestamp = datetime(
        cur_time.year, cur_time.month, cur_time.day, 0, 0
    ).timestamp()
    ss = []
    for field_value in FieldValue.objects.filter(date_value__isnull=False).filter(
        field_id__in=field_ids
    ):
        for trigger in triggers:
            if trigger.field_id == field_value.field_id:
                timestamp = get_timestamp(
                    field_value.date_value,
                    trigger.offset_type,
                    trigger.date_offset,
                    trigger.time,
                    trigger.period,
                )
                if timestamp < valid_max_timestamp and timestamp >= valid_min_timestamp:
                    s = ScheduleView(
                        timestamp=timestamp,
                        trigger_id=str(trigger.id),
                        fieldvalue_id=str(field_value.id),
                    )
                    ss.append(s)
                    count += 1
    ScheduleView.objects.bulk_create(ss)
    end_time = time.time()
    return f"elapsed_time: {end_time - start_time} and count: {count}"


@shared_task(name="read_from_db")
def read_from_db():
    start_time = time.time()

    cur_time = datetime.now()
    cur_time_till_minute = datetime(
        cur_time.year, cur_time.month, cur_time.day, cur_time.hour, cur_time.minute
    )
    timestamp = cur_time_till_minute.timestamp()

    objs = ScheduleView.objects.filter(timestamp=timestamp)
    count = len(objs)
    for obj in objs:
        # send this to kafka.
        a = 0
    objs.delete()

    end_time = time.time()
    return f"elapsed_time: {end_time - start_time} and count: {count}"


@shared_task(name="delete_from_scheduled_view")
def delete_from_scheduled_view(field_value_id, trigger_id, field_value_ids):
    start_time = time.time()

    if field_value_id:
        d = ScheduleView.objects.filter(fieldvalue_id=str(field_value_id)).delete()
    if trigger_id:
        d = ScheduleView.objects.filter(trigger_id=str(trigger_id)).delete()
    if field_value_ids:
        d = ScheduleView.objects.filter(fieldvalue_id__in=field_value_ids).delete()
    end_time = time.time()
    return f"elapsed_time: {end_time - start_time} and count: {d}"


@shared_task(name="update_scheduled_view")
def update_scheduled_view(old_data, trigger_id):
    start_time = time.time()
    t = Trigger.objects.get(id=trigger_id)
    if "field_id" in old_data and old_data.get("field_id") != t.field_id:
        fieldvalue_ids = [
            str(f.id) for f in FieldValue.objects.filter(field__id=old_data["field_id"])
        ]
        d = ScheduleView.objects.filter(fieldvalue_id__in=fieldvalue_ids).delete()
        cur_time = datetime.now()
        valid_max_timestamp = (
            datetime(cur_time.year, cur_time.month, cur_time.day, 0, 0)
            + timedelta(days=1)
        ).timestamp()
        valid_min_timestamp = datetime(
            cur_time.year, cur_time.month, cur_time.day, 0, 0
        ).timestamp()
        ss = []
        for field_value in FieldValue.objects.filter(date_value__isnull=False).filter(
            field_id=t.field_id
        ):
            timestamp = get_timestamp(
                field_value.date_value, t.offset_type, t.date_offset, t.time, t.period
            )
            if timestamp < valid_max_timestamp and timestamp >= valid_min_timestamp:
                s = ScheduleView(
                    timestamp=timestamp,
                    trigger_id=str(t.id),
                    fieldvalue_id=str(field_value.id),
                )
                ss.append(s)
        c = len(ss)
        ScheduleView.objects.bulk_create(ss)
        end_time = time.time()
        return f"elapsed_time: {end_time - start_time} and deleted_count: {d} and created_count: {c}"

    old_offset_type = t.offset_type if old_data.get("offset_type") is None else old_data.get("offset_type")
    old_offset_date = t.date_offset if old_data.get("offset_date") is None else old_data.get("offset_date")
    old_time = t.time if old_data.get("time") is None else old_data.get("time")
    old_period = t.period if old_data.get("period") is None else old_data.get("period")

    if "offset_type" in old_data and old_data.get("offset_type") != t.offset_type:
        for field_value in FieldValue.objects.filter(date_value__isnull=False).filter(
                field_id=t.field_id
        ):
            fieldvalue_ids = [
                str(f.id) for f in FieldValue.objects.filter(field__id=old_data["field_id"])
            ]
            d = ScheduleView.objects.filter(fieldvalue_id__in=fieldvalue_ids).delete()
            cur_time = datetime.now()
            valid_max_timestamp = (
                    datetime(cur_time.year, cur_time.month, cur_time.day, 0, 0)
                    + timedelta(days=1)
            ).timestamp()
            valid_min_timestamp = datetime(
                cur_time.year, cur_time.month, cur_time.day, 0, 0
            ).timestamp()
            ss = []
            old_timestamp = get_timestamp(field_value.date_value, old_offset_type, old_offset_date, old_time, old_period)