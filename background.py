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

    tomorrow = datetime.today() + timedelta(days=1)
    in_seven_days = (tomorrow + timedelta(days=7)).date()
    weekday = in_seven_days.weekday()

    institutions = api.get_institutions()
    intervals = {}

    for inst in institutions:
        intervals[inst] = api.get_intervals(inst)

    # intervals = {
    #     'Bibliotheca Albertina': [{'from': '08:00', 'until': '23:45', 'day': None},
    #                               {'from': '10:00', 'until': '18:00', 'day': '1'}],
    #     'Bibliothek Erziehungs- und Sportwissenschaft': [{'from': '08:00', 'until': '22:00', 'day': None}],
    #     'Bibliothek Klassische Archäologie /Ur-und Frühgeschichte': [
    #         {'from': '10:00', 'until': '16:00', 'day': None}],
    #     'Bibliothek Kunst': [{'from': '10:00', 'until': '16:00', 'day': None}],
    #     'Bibliothek Medizin/Naturwissenschaften': [{'from': '08:00', 'until': '23:45', 'day': None}],
    #     'Bibliothek Musik': [{'from': '10:00', 'until': '16:00', 'day': None}],
    #     'Bibliothek Rechtswissenschaft - Recht I': [{'from': '08:00', 'until': '22:00', 'day': None},
    #                                                 {'from': '10:00', 'until': '16:00', 'day': '7'}],
    #     'Bibliothek Rechtswissenschaft - Recht II': [{'from': '08:00', 'until': '22:00', 'day': None},
    #                                                  {'from': '10:00', 'until': '16:00', 'day': '7'}],
    #     'Bibliothek Regionalwissenschaften': [{'from': '10:00', 'until': '16:00', 'day': None}],
    #     'Bibliothek Veterinärmedizin': [{'from': '09:00', 'until': '18:00', 'day': None}],
    #     'Campus-Bibliothek': [{'from': '08:00', 'until': '23:45', 'day': None},
    #                           {'from': '10:00', 'until': '18:00', 'day': '1'}]
    # }

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

            api.book(credentials, preferences, str(in_seven_days))


def start():
    tomorrow = datetime.today() + timedelta(days=1)
    tomorrow = tomorrow.replace(minute=1, hour=0, second=0, microsecond=0)

    sched = BackgroundScheduler()
    sched.add_job(booking_job, 'interval', hours=24, start_date=tomorrow)
    sched.start()


if __name__ == "__main__":
    booking_job()
