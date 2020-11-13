import os
from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
application = get_wsgi_application()


from core.models import FieldValue, Trigger, Field
from core.tasks import delete_from_scheduled_view, update_scheduled_view
import argparse


def delete_date_field(field_value_id):
    if field_value_id is None:
        return
    f = FieldValue.objects.get(id=field_value_id)
    f.delete()
    delete_from_scheduled_view.delay(field_value_id, None, None)
    return "deleted field"


def update_trigger(trigger_id, field_id, offset_type, offset_date, time, period):
    if trigger_id is None:
        return
    t = Trigger.objects.get(trigger_id)
    old_t = t.copy()
    old_data = {}
    if field_id is not None:
        t.field_id = field_id
        old_data["field_id"] = field_id
    if offset_type is not None:
        t.offset_type = offset_type
        old_data["offset_type"] = old_t.offset_type

    if offset_date is not None:
        t.date_offset = offset_date
        old_data["offset_date"] = old_t.offset_date

    if time is not None:
        t.time = time
        old_data["time"] = old_t.time

    if period is not None:
        t.period = period
        old_data["period"] = old_t.period
    t.save()
    update_scheduled_view.delay(old_data, t.id)


def delete_trigger(trigger_id):
    if trigger_id is None:
        return
    t = Trigger.objects.get(id=trigger_id)
    t.delete()
    delete_from_scheduled_view.delay(None, trigger_id, None)
    return "deleted trigger"


def delete_field(field_id):
    if field_id is None:
        return
    f = Field.objects.get(id=field_id)
    f.is_active = False
    f.save()
    if f.field_type == "date":
        fv = FieldValue.objects.filter(field__id=field_id).filter()
        fv = [str(obj.id) for obj in fv]
        delete_from_scheduled_view.delay(None, None, fv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This required a field_value_id")
    parser.add_argument(
        "--field-value-id", type=int, help="field value id to delete", required=False
    )
    parser.add_argument(
        "--trigger-id", type=int, help="trigger id to delete", required=False
    )

    parser.add_argument(
        "--field-id", type=int, help="field id to delete", required=False
    )
    args, _ = parser.parse_known_args()
    delete_date_field(args.field_value_id)
    delete_trigger(args.trigger_id)
    delete_field(args.field_id)
