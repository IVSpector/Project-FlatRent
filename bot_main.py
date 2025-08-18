from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
import json
import atexit
import Check_lon_lat as coord
import os
from dotenv import load_dotenv
load_dotenv()
import model_work as model

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store user sessions
try:
    with open('tg_user_sessions.json', mode='r', encoding='utf-8') as file:
        user_sessions = json.load(file)
        user_sessions = {int(key): value for key, value in user_sessions.items()}
except:
    user_sessions = {}

def save_sessions():
    with open('tg_user_sessions.json', mode='w', encoding='utf-8') as file:
        json.dump(user_sessions, file, indent=2, ensure_ascii=False)

atexit.register(save_sessions)

# Available pages
PAGES = {
    "start": "Welcome! Let's start.",
    "enter rooms count": "Please enter the number of rooms.",
    "enter square meters": "Please enter the square meters.",
    "enter floor": "Please enter the floor number.",
    "enter house": "Please enter the house number.",
    "request location": "Check apartment price in your current location or point any location."
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    # Initialize user session
    user_sessions[user_id] = {
        "current_page": "start",
        "current_input": None,
        "data": {
            "city": None,
            "street": None,
            "house_number": None,
            "rooms": None,
            "square_meters": None,
            "floor": None,
            "location": None
        }
    }
    await update.message.reply_text(PAGES["start"])
    # Move to the next page
    user_sessions[user_id]["current_page"] = "request location"

    REPLY_BUTTONS = [[KeyboardButton(text="Send Location", request_location=True)]]

    reply_markup = ReplyKeyboardMarkup(REPLY_BUTTONS, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(PAGES["request location"], reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages based on the current page."""
    user_id = update.effective_user.id
    text = update.message.text

    if text == "Main menu":
        user_sessions[user_id]["current_page"] = "request location"
        user_sessions[user_id]["current_input"] = None
        text = "Clarify Details 🔎"

    if text == "Location":
        user_sessions[user_id]["current_page"] = "request location"
        user_sessions[user_id]["current_input"] = None
        text = "Start again 🔄"


    # Check if user has a session
    if user_id not in user_sessions:
        await update.message.reply_text("Please start with /start command.")
        return

    # Input Details: FLOOR, SQM, ROOMS
    if user_sessions[user_id]["current_input"]:

        if (text.isdigit() and int(text) < 0) or not text.isdigit():
            massage = "Please enter a number and non negative or press Main menu."
            replay_buttons = [["Main menu"]]
            reply_markup = ReplyKeyboardMarkup(replay_buttons, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(massage, reply_markup=reply_markup)

            return

        current_input = user_sessions[user_id]["current_input"]
        user_sessions[user_id]["data"][current_input] = text
        text = "Clarify Details 🔎"
        user_sessions[user_id]["current_page"] = "request location"
        user_sessions[user_id]["current_input"] = None

    current_page = user_sessions[user_id]["current_page"]
    session_data = user_sessions[user_id]["data"]

    try:
        if current_page == "details":
            if text == "Floor":
                user_sessions[user_id]["current_input"] = "floor"
                await update.message.reply_text(PAGES["enter floor"])

            elif text == "Rooms":
                user_sessions[user_id]["current_input"] = "rooms"
                await update.message.reply_text(PAGES["enter rooms count"])

            elif text == "Sq meters":
                user_sessions[user_id]["current_input"] = "square_meters"
                await update.message.reply_text(PAGES["enter square meters"])

            else:
                massage = "Please try again."
                user_sessions[user_id]["current_page"] = "request location"


                replay_buttons = [["Clarify Details 🔎"]]

                reply_markup = ReplyKeyboardMarkup(replay_buttons, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text(massage, reply_markup=reply_markup, parse_mode='Markdown')


        elif current_page == "request location":
            if text == "Start again 🔄":
                user_sessions[user_id] = {
                    "current_page": "start",
                    "current_input": None,
                    "data": {
                        "city": None,
                        "street": None,
                        "house_number": None,
                        "rooms": None,
                        "square_meters": None,
                        "floor": None,
                        "location": None
                    }
                }
                user_sessions[user_id]["current_page"] = "request location"

                reply_buttons = [[KeyboardButton(text="Send Location", request_location=True)]]

                reply_markup = ReplyKeyboardMarkup(reply_buttons, one_time_keyboard=False, resize_keyboard=True)
                await update.message.reply_text(PAGES["request location"], reply_markup=reply_markup)


            elif text == "Clarify Details 🔎":
                model_result_min, model_result_max = model.check_price(session_data)

                details = (
                    f"Current details:\n"
                    f"City: {session_data['city']}\n"
                    f"Street: {session_data['street']}\n"
                    f"House number: {session_data['house_number']}\n"
                    f"Rooms: {session_data['rooms']}\n"
                    f"Square Meters: {session_data['square_meters']}\n"
                    f"Floor: {session_data['floor']}\n"
                    f"💰 Price estimate: *{model_result_min}₪* – *{model_result_max}₪*\n"
                    # f"Please specify which detail to clarify or use /start to begin again."
                )

                replay_buttons = [["Floor", "Rooms", "Sq meters", "Location"]]
                user_sessions[user_id]["current_page"] = "details"

                reply_markup = ReplyKeyboardMarkup(replay_buttons, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text(details, reply_markup=reply_markup, parse_mode='Markdown')


            elif text == "Show Heatmap 🗺":
                with open("dashboard_telegramm.png", "rb") as photo:
                    await update.message.reply_photo(photo)
                replay_buttons = [["Clarify Details 🔎"]]
                massage = "Please clarify details about apartment to receive estimate price."

                reply_markup = ReplyKeyboardMarkup(replay_buttons, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text(massage, reply_markup=reply_markup, parse_mode='Markdown')

            return

        else:
            await update.message.reply_text("Please send your location or use /start to begin again.")

    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a valid number.")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle location messages."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text("Please start with /start command.")
        return

    if user_sessions[user_id]["current_page"] != "request location":
        await update.message.reply_text("Please complete the previous steps first.")
        return

    location = update.message.location
    user_sessions[user_id]["data"]["location"] = {
        "latitude": location.latitude,
        "longitude": location.longitude
    }

    address = coord.city_name_by_coords(user_sessions[user_id]["data"]["location"]["latitude"],
                                        user_sessions[user_id]["data"]["location"]["longitude"])


    user_sessions[user_id]["data"]["city"] = address[0]
    user_sessions[user_id]["data"]["street"] = address[1]
    user_sessions[user_id]["data"]["house_number"] = address[2]
    session_data = user_sessions[user_id]["data"]

    model_result_min, model_result_max = model.check_price(session_data)

    summary = (
        f"Thank you! Here is the collected information:\n"
        f"City: {session_data['city']}\n"
        f"Street: {session_data['street']}\n"
        f"House number: {session_data['house_number']}\n"
        f"Rooms: {session_data['rooms']}\n"
        f"Square Meters: {session_data['square_meters']}\n"
        f"Floor: {session_data['floor']}\n"
        f"💰 Price estimate: *{model_result_min}₪* – *{model_result_max}₪*\n"
    )
    # We should insert call our model to get result COMMENT
    replay_buttons = [["Start again 🔄", "Clarify Details 🔎", "Show Heatmap 🗺"]]

    reply_markup = ReplyKeyboardMarkup(replay_buttons, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')



async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Run the bot."""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == '__main__':
    main()