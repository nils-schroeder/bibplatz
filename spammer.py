from queue import Queue
from threading import Thread
import time
import logging
from random import randint
import aws
import api
from telegram import Bot
import os

TOKEN = os.environ["TELEGRAM_TOKEN"]

logger = logging.getLogger(__name__)
q = Queue()

error_dict = {
    "outofdate": "Außerhalb der Öffnungszeiten",
    "outoftime": "Außerhalb der Öffnungszeiten",
    "outofreach": "Du kannst nur 7 Tage im voraus buchen",
    "concurrently_booking": "Du hast bereits eine Buchung in diesem Zeitraum",
}


def send_message(chat_id, msg):
    try:
        bot = Bot(TOKEN)
        bot.sendMessage(chat_id, msg)

    except Exception:
        logger.error(f"Error sending message to {chat_id}")


def run_request():
    while True:
        spam_request = q.get()
        try_booking(spam_request)


def try_booking(spam_request):

    logger.info(f"Running spam request for {spam_request['chat_id']}")
    running = True
    data = aws.get_raw_data(spam_request["chat_id"])
    credentials = data["credentials"]
    preferences = spam_request["prefs"]
    date_string = spam_request["date_string"]

    while running:
        try:

            result = api.book(credentials, preferences, date_string)

            if result:
                msg = str(result["message"])
                if result["bookingCode"]:

                    logger.info(f"Sucessfully booked {result['bookingCode']} for {spam_request['chat_id']}")
                    send_message(spam_request['chat_id'], f"Du hast Platz {result['workspaceId']} gebucht.")
                    running = False

                elif not (msg.startswith("info#") or msg == ""):

                    try:
                        error_msg = error_dict[msg]
                    except Exception:
                        error_msg = "Unbekannt"
                        logger.warning(f"Unknown error message {msg}")

                    logger.warning(f"Invalid request from {spam_request['chat_id']}")
                    send_message(spam_request['chat_id'], f"Leider war deine Anfrage fehlerhaft.\n"
                                                          f"Fehler: {error_msg}")
                    running = False


        except Exception:
            logger.error(f"Error while booking for {spam_request['chat_id']}")
            send_message(spam_request['chat_id'], "Leider ist beim bearbeiten deiner Anfrage ein Fehler aufgetreten.\n"
                                                  "Bitte versuche es erneut.")
            running = False

        time.sleep(10 + randint(0, 5))


def add_request(spam_request):
    q.put(spam_request)
    logger.info(spam_request)


def start():
    t = Thread(target=run_request)
    t.start()