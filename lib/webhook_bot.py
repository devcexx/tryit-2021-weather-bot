import json
import bot
from telebot.types import Update


def check_bot_token(event):
    """ Verify that the bot token is available on the resource path
    and it's valid """
    path_params = event.get("pathParameters")
    if path_params is None:
        return False

    return path_params.get("token") == bot.bot.token


def handler(event, _context):
    # Prevent calls to the bot that doesn't come from Telegram.
    if not check_bot_token(event):
        print("Invalid bot token received. Unauthorized")
        return {
            "statusCode": 403,
            "body": json.dumps("Unauthorized")
        }

    body = json.loads(event["body"])

    update = Update.de_json(body)
    bot.bot.process_new_updates([update])

    return {
        "statusCode": 200,
        "body": "{}"
    }
