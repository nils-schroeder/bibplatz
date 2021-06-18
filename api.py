import requests


def check_credentials(payload):
    session = requests.Session()

    post = session.post('https://seats.ub.uni-leipzig.de/api/booking/login', data=payload)

    response = post.json()

    session.close()

    return str(response["msg"])


def get_institutions():
    session = requests.Session()

    get = session.get('https://seats.ub.uni-leipzig.de/api/booking/institutions')
    get.encoding = 'utf-8'

    response = get.text.split("#")

    session.close()

    return response


def get_areas(institution):
    session = requests.Session()

    get = session.get(f'https://seats.ub.uni-leipzig.de/api/booking/areas?institution={institution}')
    get.encoding = 'utf-8'

    response = get.text.split("#")

    session.close()

    response.append("no selection")
    return response


def get_intervals(institution):
    session = requests.Session()

    get = session.get(f'https://seats.ub.uni-leipzig.de/api/booking/timeslots?institution={institution}')

    response = get.json()

    session.close()

    return response["interval"]


def prettfiy_intervals(intervals):
    day_map = {
        "1": "Sonntag",
        "2": "Montag",
        "3": "Dienstag",
        "4": "Mittwoch",
        "5": "Donnerstag",
        "6": "Freitag",
        "7": "Samstag",
    }

    pretty_string = ""

    for interval in intervals:
        if not interval["day"]:
            pretty_string += f"{interval['from']} Uhr - {interval['until']} Uhr \n"
        else:
            pretty_string += f"{day_map[str(interval['day'])]}: {interval['from']} Uhr - {interval['until']} Uhr"

    return pretty_string


def get_fittings():
    fittings = ["Fertig", "mit Strom", "PC", "kein PC", "LAN", "Steharbeitsplatz"]
    return fittings


def book(credentials, preferences, date_string):
    payload_login = {
        "readernumber": credentials["readernumber"],
        "password": credentials["password"],
        "logintype": 0
    }

    session = requests.Session()

    login = session.post('https://seats.ub.uni-leipzig.de/api/booking/login', data=payload_login)

    token = login.json()["token"]

    payload_booking = {
        "institution": preferences["institution"],
        "area": preferences["area"],
        "fitting": preferences["fitting"],
        "from_time": preferences["from_time"],
        "until_time": preferences["to_time"],
        "from_date": date_string,
        "tslot": 0,
        "preference": 0,
        "readernumber": credentials["readernumber"],
        "token": token
    }

    booking = session.post('https://seats.ub.uni-leipzig.de/booking-internal/booking/booking', data=payload_booking)

    result = booking.json()

    session.close()

    return result
