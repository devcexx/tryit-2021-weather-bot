import telebot
import boto3
import typing
from util import get_environ
from telebot.types import Message, InlineKeyboardButton, \
    InlineKeyboardMarkup, CallbackQuery
from database import DynamoDatabase
from database.model import TemperatureUnit, UserSettings
import weather_api
from weather_api import Weather

BOT_DDB_TABLE = "DDB_TABLE"
BOT_TOKEN_ENVIRON_NAME = "BOT_TOKEN"

dynamodb = boto3.resource("dynamodb")

# Disable threading for making it compatible with a Lambda.
# Polling will be only used for testing, so it's fine.
bot = telebot.TeleBot(get_environ(BOT_TOKEN_ENVIRON_NAME),
                      parse_mode="Markdown", threaded=False)

database = DynamoDatabase(dynamodb.Table(get_environ(BOT_DDB_TABLE)))


def kelvin_to_celsius(kelvin: float) -> float:
    return kelvin - 273.15


def kelvin_to_fahrenheit(kelvin: float) -> float:
    return (9.0 * (kelvin - 273.15)) / 5.0 + 32.0


def ensure_priv_chat(message: Message) -> bool:
    if message.chat.type != "private":
        bot.reply_to(message, "This bot only works on private chats!")
        return False
    return True


@bot.message_handler(commands=["start"])
def handle_start(message: Message):
    if not ensure_priv_chat(message):
        return

    bot.reply_to(message, "Hi! Send me a location marker or the name of "
                 "a city and I'll reply to you with the current location "
                 "in that place.")


def send_weather_message(user: int, weather: Weather):
    global database

    user_settings = database.settings_dao() \
                            .fetch_settings_or_default(user)

    # API uses Kelvin by default
    if user_settings.temp_unit == TemperatureUnit.Celsius:
        degrees = lambda x: "%.1f °C" % kelvin_to_celsius(x)
    else:
        degrees = lambda x: "%.1f °F" % kelvin_to_fahrenheit(x)

    weather_code = weather.weather[0]
    anim_name = weather_api.image_name_for_weather_code(weather_code)

    caption = f"*Place*: {weather.name}\n"
    caption += f"*Weather*: {weather_code.description}\n"
    caption += f"*Temperature*: {degrees(weather.main.temp)} " \
        f"(feels like {degrees(weather.main.feels_like)})\n"

    caption += f"*Humidity*: {weather.main.humidity}%"

    with open(f"animations/{anim_name}.mp4", "rb") as anim:
        bot.send_animation(user, anim, caption=caption)


def send_weather_info_not_found_message(user: int):
    bot.send_message(user, "Couldn't find weather information for that place!")


@bot.message_handler(commands=["settings"])
def handle_settings_command(message: Message):
    global database

    if not ensure_priv_chat(message):
        return

    user_settings = database.settings_dao() \
                            .fetch_settings_or_default(message.from_user.id)

    send_settings_message(message.from_user.id, user_settings)


def handle_weather_request(message: Message, weather_fun):
    if not ensure_priv_chat(message):
        return

    user_id = message.from_user.id
    weather = weather_fun()

    if weather is None:
        send_weather_info_not_found_message(user_id)
    else:
        send_weather_message(user_id, weather)


@bot.message_handler(content_types=["text"])
def handle_text_message(message: Message):
    handle_weather_request(message, lambda: weather_api
                           .weather_request_from_place_name(message.text))


@bot.message_handler(content_types=["location"])
def handle_message(message: Message):
    location = message.location
    handle_weather_request(message, lambda: weather_api
                           .weather_request_from_location(
                               location.latitude,
                               location.longitude))


def send_settings_message(user: int, settings: UserSettings,
                          edit_message: typing.Optional[Message] = None):
    text = "*Settings*\n\n"
    text += f"🌡 *Temperature unit*: {settings.temp_unit.to_str()}"

    if settings.temp_unit == TemperatureUnit.Fahrenheit:
        alternate_unit = TemperatureUnit.Celsius
    else:
        alternate_unit = TemperatureUnit.Fahrenheit

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(f"Switch to {alternate_unit.to_str()}",
                                      callback_data="toggle-temp-unit"))

    if edit_message is None:
        bot.send_message(user, text, reply_markup=keyboard)
    else:
        bot.edit_message_text(text,
                              chat_id=edit_message.chat.id,
                              message_id=edit_message.message_id,
                              reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "toggle-temp-unit")
def handle_callback_query(call: CallbackQuery):
    global database
    user_id = call.from_user.id

    user_settings = database.settings_dao() \
                            .fetch_settings_or_default(user_id)

    if user_settings.temp_unit == TemperatureUnit.Celsius:
        user_settings.temp_unit = TemperatureUnit.Fahrenheit
    else:
        user_settings.temp_unit = TemperatureUnit.Celsius

    database.settings_dao() \
            .update_settings(user_settings)

    send_settings_message(user_id,
                          user_settings,
                          edit_message=call.message)
