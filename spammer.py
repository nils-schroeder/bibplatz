from queue import Queue
from threading import Thread
import time
import logging
from random import randint
import aws
import api

logger = logging.getLogger(__name__)
q = Queue()


def run_request():
    while True:
        spam_request = q.get()
        try_booking(spam_request)


def try_booking(spam_request):
    logger.log(f"Running spam request  for {spam_request['chat_id']}")
    running = True
    data = aws.get_data(spam_request["chat_id"])
    credentials = data["credentials"]
    preferences = spam_request["prefs"]
    date_string = spam_request["date_string"]

    while running:

        result = api.book(credentials, preferences, date_string)


        time.sleep(10 + randint(0, 5))


def add_request(spam_request):
    q.put(spam_request)
    logger.info(spam_request)


def start():
    t = Thread(target=run_request)
    t.start()

