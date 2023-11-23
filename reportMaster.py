"""Report errors to Telegram"""
import telebot

from config import BOT_TELEGRAM_TOKEN, ENABLE_UNITS, HUMAN_ID

# List of codes and messages
templates = (
    {"code": "Wrong Code",
        "type": "ERROR",
        "message": "report funcion recived wrond errorCode"},
    
    {"code": "Torrents list 404",
        "type": "FATAL",
        "message": "fail to load torrents list page"},
    
    {"code": "Torrents list parse error",
        "type": "FATAL",
        "message": "fail to parse torrents list on page"},
    
    {"code": "Torrent page 404",
        "type": "ERROR",
        "message": "fail to load torrent page"},
    
    {"code": "Torrent page parse error",
        "type": "ERROR",
        "message": "fail to parse info on torrent page"},
    
    {"code": "No new torrents",
        "type": "CHECK",
        "message": "no new torrents"},

    {"code": "No game genre",
        "type": "ERROR",
        "message": "can't find synonim for game genre"},

    {"code": "No YouTube video",
        "type": "ERROR",
        "message": "can't find YouTube video"},

    {"code": "YouTube download fail",
        "type": "ERROR",
        "message": "can't download YouTube video"},

    {"code": "No torrent screenshots",
        "type": "ERROR",
        "message": "fail to parse screenshots"},

    {"code": "No crawler for image",
        "type": "ERROR",
        "message": "no crawler for image hoster"},

    {"code": "Image 404",
        "type": "ERROR",
        "message": "fail to download image"},

    {"code": "Complete",
        "type": "INFO",
        "message": "run complete, items: +"},

    {"code": "DB write fail",
        "type": "ERROR",
        "message": "fail to send data to DB"},

    {"code": "DB read fail",
        "type": "FATAL",
        "message": "fail to read data from DB"},

    {"code": "Metacritic SERP 404",
        "type": "ERROR",
        "message": "fail to load SERP"},

    {"code": "Metacritic no item",
        "type": "ERROR",
        "message": "item not found"},

    {"code": "Metacritic item 404",
        "type": "ERROR",
        "message": "fail to load item page"},

    {"code": "No torrents parsed",
        "type": "FATAL",
        "message": "fail to parse all torrents, total: "},

    {"code": "Cleanup",
        "type": "INFO",
        "message": "cleanup complete, removed: -"},

    {"code": "No origin",
        "type": "ERROR",
        "message": "Weekly watchdog can't find origin"},
)

# Send Telegram message to master
def send_telegram_report(message, disableSound=False):

    if ENABLE_UNITS['tgBot']:
        bot = telebot.TeleBot(BOT_TELEGRAM_TOKEN)
        
        try:
            bot.send_message(HUMAN_ID,
                            message,
                            disable_notification=disableSound,
                            parse_mode="HTML")
        except:
            print("Can't send TG Report")
            return False
    else:
        print(message)
    
    return True

# Prepare and send report
def report(error_code, sender, additional=''):

    # Find error code
    code = next((i for i, item in enumerate(templates) if item["code"] == error_code), 0)

    # Add comma before additional info if it's exist
    if additional:
        additional = ', ' + additional

    # Generate message and sound
    message = templates[code]['type'] + ': ' + sender + ', ' + templates[code]['message'] + additional
    disable_sound = True if templates[code]['type'] in ['CHECK', 'INFO',] else False

    # Send report
    if send_telegram_report(message, disable_sound):
        return True

    return False