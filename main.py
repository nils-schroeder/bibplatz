import logging
import api
import aws
import background
import os
import spammer
from datetime import datetime
from telegram import InlineKeyboardButton, ReplyKeyboardRemove, Update, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_TOKEN"]

BIBID, BIBPW = range(2)
INSTITUTION, AREA, FITTING, FROM_TIME, TO_TIME = range(5)
NOW_INSTITUTION, NOW_AREA, NOW_FITTING, NOW_DATE, NOW_FROM_TIME, NOW_TO_TIME = range(6)


def start(update: Update, context: CallbackContext):
    logger.info("User %s created an account", update.message.chat_id)
    aws.create_user(update.message.chat_id)
    update.message.reply_text(
        "Benutze /login um deine Logindaten zu hinterlegen\n"
        "Benutze /settings um deine Einstellungen zu hinterlegen\n"
        "Mit /help kannst du dir Hilfe anzeigen lassen\n"
    )


def help_command(update: Update, context: CallbackContext):
    logger.info("Helping %s", update.message.chat_id)
    update.message.reply_text(
        "/login - Gebe deine Nutzerdaten ein\n"
        "/settings - Bearbeitet deine Voreinstellungen\n"
        "/on - Start die automatischen Buchungen\n"
        "/off - Stoppe die automatischen Buchungen\n"
        "/show - Zeigt deine aktuellen Einstellungen\n"
    )


def login(update: Update, context: CallbackContext):
    update.message.reply_text("Bitte gebe deine Bibliotheksnummer ein")
    return BIBID


def bib_id(update: Update, context: CallbackContext):
    context.user_data["readernumber"] = update.message.text

    update.message.reply_text("Bitte gebe dein Passwort ein")

    return BIBPW


def bib_pw(update: Update, context: CallbackContext):
    context.user_data["password"] = update.message.text

    payload = {
        "readernumber": context.user_data["readernumber"],
        "password": context.user_data["password"],
        "logintype": 0
    }

    result = api.check_credentials(payload)

    if result == "":
        update.message.reply_text("Super, das hat geklappt!")

        creds = {
            "readernumber": context.user_data["readernumber"],
            "password": context.user_data["password"],
        }

        aws.update_credentials(update.message.chat_id, creds)

    else:
        update.message.reply_text(f"Es gab einen Fehler: {result}")

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    logger.info("User %s canceled the conversation.", update.message.chat_id)
    update.message.reply_text(
        'Ciao Kakao!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def preferences(update: Update, context: CallbackContext):
    institutions = api.get_institutions()

    keyboard = [[InlineKeyboardButton(i, callback_data=str(i))] for i in institutions]

    update.message.reply_text("Bitte w??hle einen Standort",
                              reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))

    return INSTITUTION


def institution(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data["institution"] = query.data

    areas = api.get_areas(context.user_data["institution"])

    keyboard = [[InlineKeyboardButton(a, callback_data=str(a))] for a in areas]

    query.answer()
    query.edit_message_text("Bitte w??hle eine Area",
                            reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))

    return AREA


def area(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data["area"] = query.data

    context.user_data["fitting"] = []
    context.user_data["no_selected_fitting"] = api.get_fittings()

    keyboard = [[InlineKeyboardButton(f, callback_data=str(f))] for f in api.get_fittings()]

    query.answer()
    query.edit_message_text("Bitte w??hle eine Ausstattung",
                            reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))

    return FITTING


def fitting(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.data == "Fertig":
        intervals = api.get_intervals(context.user_data["institution"])
        pretty_intervals = api.prettfiy_intervals(intervals)
        query.answer()
        query.edit_message_text(f"{pretty_intervals}\n\nBitte gebe eine Startzeit ein (hh:mm)")
        return FROM_TIME

    else:
        context.user_data["fitting"].append(query.data)
        context.user_data["no_selected_fitting"].remove(query.data)
        keyboard = [[InlineKeyboardButton(f, callback_data=str(f))] for f in context.user_data["no_selected_fitting"]]

        query.answer()
        query.edit_message_text("Bitte w??hle weitere Ausstattung",
                                reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))
        return FITTING


def from_time(update: Update, context: CallbackContext):
    context.user_data["from_time"] = update.message.text

    update.message.reply_text("Bitte gebe eine Endzeit ein")
    return TO_TIME


def to_time(update: Update, context: CallbackContext):
    context.user_data["to_time"] = update.message.text

    # intervals = api.get_intervals(context.user_data["institution"])

    update.message.reply_text(
        "Das wars!\n\n"
        "Schalte den Bot jetzt mit /on an."
    )

    prefs = {"institution": context.user_data["institution"],
             "area": context.user_data["area"],
             "fitting": context.user_data["fitting"],
             "from_time": context.user_data["from_time"],
             "to_time": context.user_data["to_time"]
             }

    aws.update_preferences(update.message.chat_id, prefs)

    return ConversationHandler.END


def now(update: Update, context: CallbackContext):
    institutions = api.get_institutions()

    keyboard = [[InlineKeyboardButton(i, callback_data=str(i))] for i in institutions]

    update.message.reply_text("Bitte w??hle einen Standort",
                              reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))

    return NOW_INSTITUTION


def now_institution(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data["now_institution"] = query.data

    areas = api.get_areas(context.user_data["now_institution"])

    keyboard = [[InlineKeyboardButton(a, callback_data=str(a))] for a in areas]

    query.answer()
    query.edit_message_text("Bitte w??hle eine Area",
                            reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))

    return NOW_AREA


def now_area(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data["now_area"] = query.data

    context.user_data["now_fitting"] = []
    context.user_data["now_no_selected_fitting"] = api.get_fittings()

    keyboard = [[InlineKeyboardButton(f, callback_data=str(f))] for f in api.get_fittings()]

    query.answer()
    query.edit_message_text("Bitte w??hle eine Ausstattung",
                            reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))

    return NOW_FITTING


def now_fitting(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.data == "Fertig":
        intervals = api.get_intervals(context.user_data["now_institution"])
        pretty_intervals = api.prettfiy_intervals(intervals)
        query.answer()
        query.edit_message_text(f"{pretty_intervals}\n\nBitte gebe ein Datum an (dd.mm.yyyy)")
        return NOW_DATE

    else:
        context.user_data["now_fitting"].append(query.data)
        context.user_data["now_no_selected_fitting"].remove(query.data)
        keyboard = [[InlineKeyboardButton(f, callback_data=str(f))] for f in
                    context.user_data["now_no_selected_fitting"]]

        query.answer()
        query.edit_message_text("Bitte w??hle weitere Ausstattung",
                                reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))
        return NOW_FITTING


def now_date(update: Update, context: CallbackContext):

    context.user_data["now_date"] = str(datetime.strptime(update.message.text, "%d.%m.%Y").date())

    update.message.reply_text("Bitte gebe eine Startzeit ein (hh:mm)")
    return NOW_FROM_TIME


def now_from_time(update: Update, context: CallbackContext):
    context.user_data["now_from_time"] = update.message.text

    update.message.reply_text("Bitte gebe eine Endzeit ein")
    return NOW_TO_TIME


def now_to_time(update: Update, context: CallbackContext):
    context.user_data["now_to_time"] = update.message.text

    update.message.reply_text(
        "Das wars\n\n"
        "Der Bot benachrichtigt dich, wenn ein Platz gefunden wurde."
    )
    spam_req = {
        "chat_id": update.message.chat_id,
        "date_string": context.user_data["now_date"],
        "prefs": {"institution": context.user_data["now_institution"],
                  "area": context.user_data["now_area"],
                  "fitting": context.user_data["now_fitting"],
                  "from_time": context.user_data["now_from_time"],
                  "to_time": context.user_data["now_to_time"]
                  }
    }

    spammer.add_request(spam_req)

    return ConversationHandler.END


def on(update: Update, context: CallbackContext):
    aws.update_active(update.message.chat_id, True)

    update.message.reply_text(
        "Die automatische Buchung ist jetzt eingeschaltet"
    )


def off(update: Update, context: CallbackContext):
    aws.update_active(update.message.chat_id, False)

    update.message.reply_text(
        "Die automatische Buchung ist jetzt ausgeschaltet"
    )


def show(update: Update, context: CallbackContext):
    update.message.reply_text(aws.get_data(update.message.chat_id))


def main() -> None:
    background.start()
    spammer.start()

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    credentials_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            BIBID: [MessageHandler(Filters.text, bib_id)],
            BIBPW: [MessageHandler(Filters.text, bib_pw)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    preferences_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", preferences)],
        states={
            INSTITUTION: [CallbackQueryHandler(institution)],
            AREA: [CallbackQueryHandler(area)],
            FITTING: [CallbackQueryHandler(fitting)],
            FROM_TIME: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), from_time)],
            TO_TIME: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), to_time)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    book_now_handler = ConversationHandler(
        entry_points=[CommandHandler("now", now)],
        states={
            NOW_INSTITUTION: [CallbackQueryHandler(now_institution)],
            NOW_AREA: [CallbackQueryHandler(now_area)],
            NOW_FITTING: [CallbackQueryHandler(now_fitting)],
            NOW_DATE: [MessageHandler(Filters.regex('^(3[01]|[12][0-9]|0?[1-9])\.(1[012]|0?[1-9])\.((?:19|20)\d{2})$'),
                                      now_date)],
            NOW_FROM_TIME: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), now_from_time)],
            NOW_TO_TIME: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), now_to_time)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('on', on))
    dispatcher.add_handler(CommandHandler('off', off))
    dispatcher.add_handler(CommandHandler('show', show))

    dispatcher.add_handler(credentials_handler)
    dispatcher.add_handler(preferences_handler)
    dispatcher.add_handler(book_now_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
