from django_q.models import Schedule
from django.utils.timezone import now
from datetime import timedelta

def run():
    now_dt = now()
    run_time_today = now_dt.replace(hour=23, minute=59, second=0, microsecond=0)
    if now_dt >= run_time_today:
        run_time_today += timedelta(days=1)

    schedule, created = Schedule.objects.get_or_create(
        name="Update booking status nightly",
        defaults={
            'func': 'trip_package.tasks.update_booking_status',
            'schedule_type': Schedule.DAILY,  
            'next_run': run_time_today,
        }
    )

    if created:
        print("Schedule created successfully.")
    else:
        print("Schedule already exists.")
