import bot
import traceback

# Keep the bot alive in case of an unhandled error
while True:
    try:
        bot.bot.polling()
        break  # Quit if exits normally
    except KeyboardInterrupt:
        break
    except Exception:
        traceback.print_exc()
