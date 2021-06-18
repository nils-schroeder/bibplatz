from datetime import datetime, timedelta
import api
import aws
import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


def is_valid(user):
    if not user["enabled"]:
        return False

    creds = user["credentials"]
    prefs = user["preferences"]

    if creds["readernumber"] == "" or creds["password"] == "":
        return False

    if prefs["institution"] == "" or prefs["area"] == "" or prefs["from_time"] == "" or prefs["to_time"] == "":
        return False

    return True


def booking_job():
    users = aws.get_all_users()

    today = datetime.today()
    in_seven_days = (today + timedelta(days=7)).date()
    weekday = in_seven_days.weekday()

    institutions = api.get_institutions()
    intervals = {}

    for inst in institutions:
        intervals[inst] = api.get_intervals(inst)

    for user in users:
        if is_valid(user):

            logger.info("Booking for user %s", user["chat_id"])

            credentials = user["credentials"]
            preferences = user["preferences"]

            from_time = datetime.strptime(preferences["from_time"], "%H:%M").time()
            until_time = datetime.strptime(preferences["to_time"], "%H:%M").time()

            for interval in intervals[preferences["institution"]]:
                interval_from = datetime.strptime(interval["from"], "%H:%M").time()
                interval_until = datetime.strptime(interval["until"], "%H:%M").time()
                if interval["day"]:
                    if int(interval["day"]) == weekday:
                        if from_time < interval_from:
                            from_time = interval_from
                        if until_time > interval_until:
                            until_time = interval_until
                else:
                    if from_time < interval_from:
                        from_time = interval_from
                    if until_time > interval_until:
                        until_time = interval_until

            preferences["from_time"] = from_time.strftime("%H:%M")
            preferences["to_time"] = until_time.strftime("%H:%M")

            result = api.book(credentials, preferences, str(in_seven_days))

            logger.info(result)


def start():
    today = datetime.today()
    today = today.replace(minute=1, hour=0, second=0, microsecond=0)

    sched = BackgroundScheduler()
    sched.add_job(booking_job, 'interval', hours=24, start_date=today)
    sched.start()
