import os

# DB connection options
DB_OPTIONS = {
  'host': 'localhost',
  'user': 'root',
  'password': '',
  'database': 'flint'
}

# Report bot api key
BOT_TELEGRAM_TOKEN = 'SECRET'
BOT_WEEKLY_LINKS_WATCHER_TOKEN = 'SECRET'

# Telegram ID for bot reports
HUMAN_ID = '323091598'

# Trackers list of torrents URLs
TRACKERS = {
    'rutracker_games': 'https://rutracker.org/forum/viewforum.php?f=635&sort=2',
}

# Paths to directories
APP_PATH = os.path.abspath(os.path.dirname(__file__))
IMG_PATH = APP_PATH + "/../media/images/"
VIDEO_PATH = APP_PATH + "/../media/video/"

# How long to keep media files
MEDIA_EXPIRE_DAYS = 14

# Debug
ENABLE_UNITS = {
    'video': True,
    'images': True,
    'tgBot': True,
    'dbWrite': True,
    'Metacritic': True,
}