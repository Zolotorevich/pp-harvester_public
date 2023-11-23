from time import sleep

import mysql.connector
from origamibot import OrigamiBot as Bot
from origamibot.listener import Listener

from config import BOT_WEEKLY_LINKS_WATCHER_TOKEN, DB_OPTIONS
from logger import log
from reportMaster import report

# Channels for watching
CHANNELS = [
    {'channelID': -1001850836144, 'className': 'Games'}, # @flint_games
]

class Weekly():

    def __init__(self, messageID, title):

        # Save message id and title in weekly table
        query = (   f"INSERT INTO {self.weeklyTable} (messageID, owner_id) "
                    f"SELECT %s, id FROM {self.originTable} "
                    "WHERE title LIKE %s ORDER BY id DESC LIMIT 1"
                 )
        params = (messageID, title)
        rows_affected = 0

        log('Telegram links watcher', 'INFO', 'Writing new ' + str(self.__class__.__name__))

        try:
            connection = mysql.connector.connect(**DB_OPTIONS)
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            rows_affected = cursor.rowcount
            cursor.close()

        except mysql.connector.Error as error:
            log('Telegram links watcher', 'ERROR', "Failed to insert record into table {}".format(error))
            report('DB write fail',
                               self.__class__.__name__,
                               str(error) + ' ' + str(messageID) + ' ' + str(title))
            print("Failed to insert record into table {}".format(error))

        finally:
            if connection.is_connected():
                connection.close()

        # Foreign key not found, report
        if not rows_affected:
            log('Telegram links watcher', 'ERROR', 'No rows affected')
            report('No origin', self.__class__.__name__, str(messageID) + ' ' + str(title))

class Games(Weekly):
    weeklyTable = 'games_weekly'
    originTable = 'games_games'


class MessageListener(Listener):
    def __init__(self, bot):
        self.bot = bot

    def on_channel_post(self, message):

        log('Telegram links watcher', 'INFO', 'New message: ' + str(message))

        # Check if message have media caption
        if message.caption:

            log('Telegram links watcher', 'INFO', 'Message have caption')
            
            # Get message title
            title = message.caption[:message.caption.find('\n')]

            log('Telegram links watcher', 'INFO', "Message title: " + title)

            # Find and create weekly item object
            for channel in CHANNELS:
                if message.chat.id == channel['channelID']:
                    item_class = globals()[channel['className']]
                    weekly_item = item_class(message.message_id, title)
                    break
            else:
                log('Telegram links watcher', 'ERROR', 'Channel not found')

        else:
            log('Telegram links watcher', 'INFO', "Message don't have caption")


if __name__ == '__main__':

    # Create bot
    bot = Bot(BOT_WEEKLY_LINKS_WATCHER_TOKEN)

    # Add an event listener
    bot.add_listener(MessageListener(bot))

    # Start bot
    bot.start()
    while True:
        sleep(1)