import mysql.connector
import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL

from config import DB_OPTIONS, ENABLE_UNITS, VIDEO_PATH
from reportMaster import report


# Request website -> str:html
def get_page(url, encoding='utf-8'):
    headers = {
        'User-Agent' : 'Mozilla/5.0',
        'Content-Type' : 'text/html;'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    # Set encoding
    response.encoding = encoding

    return response.text

# Find and download YouTube video -> {url, filename}
def download_video(query):

    if not ENABLE_UNITS['video']:
        print('Simulated find and download YouTube video ' + query)
        return ''

    # HOTFIX Local scope variable, otherwise filename_hook not working
    # TODO Rebuild this Function as Class
    filename = ''

    # Hook for getting filename after download complete
    def filename_hook(info):
        nonlocal filename
        if info['status'] == 'finished':
            filename = info['filename']

    # Hook for download video shorter than 600 seconds
    def longer_than_a_minute(info, *, incomplete):
        duration = info.get('duration')
        if duration and duration > 600:
            return 'The video is too long'

    # YT-DL options
    ydl_opts = {
        'outtmpl': VIDEO_PATH + '%(id)s.%(ext)s',
        'noplaylist':'True',
        'match_filter': longer_than_a_minute,
        'progress_hooks': [filename_hook]
    }

    # Find video
    with YoutubeDL(ydl_opts) as ydl:
        try:
            video = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            url = 'https://www.youtube.com/watch?v=' + video['id']
        except:
            # Send error report
            report('No YouTube video', 'YoutubeDL', query)
            return False

        try:
            # Download video
            ydl.download(url)
        except:
            # Send error report
            report('YouTube download fail', 'YoutubeDL', query)
            return False

    return {'url': url, 'filename': filename[filename.rfind('/') + 1:]}

# Delete trash symbols from torrent raw text -> str
def optimize_raw_text(tracker, text):

    if tracker == 'rutracker':
        # Find and delete footer
        text = text[:text.find('Как качать\nFAQ\nПокраснели раздачи?')]

        # Delete double new lines
        while '\n\n' in text:
            text = text.replace('\n\n', '\n')

        # Delete new line after ':'
        # TODO change to regExp (':' + any spaces + '\n')
        text = text.replace(':\n', ':').replace(': \n', ':')
    
    return text

# Find value in text like 'RAM: 8 Gb' -> '8 Gb'
def find_value(text, value, removePunctuation=True):

    try:
        # Try to find value
        start_point = text.lower().find(value.lower()) + len(value)

        # Check if found value
        if start_point == len(value) - 1:
            return ''
        
        text = text[start_point:text.find('\n', start_point)].strip()

        # Check if parsed ':' at beginin
        if text[0] == ':':
            text = text[1:]

        # Remove punctuation in the end
        if text[-1] in (';', '.', ',') and removePunctuation:
            return text[:-1]
    except:
        return ''

# Replace 'GB' with 'Гб' -> str
def optimize_GPU(text):
    # Replace Gb with Гб
    for item in ('GB', 'Gb', 'gb', 'ГБ', 'гб',):
        if item in text:
            text = text.replace(item, 'Гб')
            break

    # Remove AMD and nVidia
    for item in ('AMD ', 'amd ', 'nvidia ', 'nVidia ', 'NVIDIA ', 'Nvidia '):
        if item in text:
            text = text.replace(item, '')
    
    return text

# Replace 'a|b' with 'a, b' and delete trash symbold like '™'
def remove_trash_symbols(text):
    trash_symbols = [
        {'trash': ' /', 'replacement': ','},
        {'trash': '/', 'replacement': ', '},
        {'trash': ' |', 'replacement': ','},
        {'trash': '|', 'replacement': ', '},
        {'trash': '™', 'replacement': ''},
        {'trash': '®', 'replacement': ''},
        {'trash': ' или эквивалентный', 'replacement': ''},
        {'trash': ' или эквивалентная', 'replacement': ''},
        {'trash': ' or equivalent', 'replacement': ''},
        {'trash': ' [требуется поддержка AVX инструкций]', 'replacement': ''},
        {'trash': ' or above', 'replacement': ''},
        {'trash': ' or better', 'replacement': ''},
        {'trash': ' or ', 'replacement': ', '},
        {'trash': ' или ', 'replacement': ', '},
    ]

    for symbol in trash_symbols:
        if symbol['trash'] in text:
            text = text.replace(symbol['trash'], symbol['replacement'])

    return text

# Get Metacritic score for title -> {int || None}
# Available types: game.
# TODO add more types, now it's checks only PC games
def metacritic_score(type, title):
    rating = {
        'critics': None,
        'users': None
        }

    if not ENABLE_UNITS['Metacritic']:
        print('Simulated Metacritic score for ' + title)
        return rating
    
    # Get SERP
    html = get_page('https://www.metacritic.com/search/game/'
                    + title.replace('(2)', '')
                    + '/results?sort=recent&plats[3]=1&search_type=advanced')
    
    # Get games headers from SERP
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        items_headers = soup.find_all('h3', class_='product_title')

        # Find PC game
        for header in items_headers:
            header_href = header.find('a').get('href')
            if '/pc/' in header_href:
                # Get item page
                html = get_page('https://www.metacritic.com' + header_href)

                # Get ratings
                if html:
                    soup = BeautifulSoup(html, 'html.parser')

                    # Critics rating
                    critic_score = soup.select('span[itemprop="ratingValue"]')
                    if critic_score:
                        # Check if its number
                        try:
                            rating['critics'] = int(critic_score[0].text)
                        except:
                            pass

                    # Users rating
                    user_score = soup.select('div.metascore_w.user.large.game')
                    if user_score:
                        # Check if its number
                        try:
                            rating['users'] = int(user_score[0].text.replace('.',''))
                        except:
                            pass
                    
                else:
                    # Can't get item page
                    report('Metacritic item 404', 'Metacritic', title + ': ' + header_href)

                # Stop finding PC game
                break
        else:
            # No PC game
            report('Metacritic no item', 'Metacritic', title)
    else:
        # Can't get serach page
        report('Metacritic SERP 404', 'Metacritic', title)

    return rating

# Replace game genre by infinitive from DB
def normalize_genre(text):

    try:
        # Create a list with input values
        genres_list = text.split(', ')

        # Check if it was split by '/'
        if len(genres_list) == 1:
            genres_list = text.split(' / ')

        # Find and replace genres
        query = (   "SELECT genre FROM games_genre "
                    "JOIN games_genresynonym ON games_genre.id = games_genresynonym.owner_id "
                    "WHERE games_genresynonym.synonym LIKE %s "
                    "UNION "
                    "SELECT genre FROM games_genre WHERE genre LIKE %s"
                )

        for i, genre in enumerate(genres_list):
            try:
                connection = mysql.connector.connect(**DB_OPTIONS)
                cursor = connection.cursor()
                cursor.execute(query, (genre, genre))
                result = cursor.fetchall()

                # Update list
                if result:
                    genres_list[i] = result[0][0]
                else:
                    # Report error
                    report('No game genre', 'Normalize Genre function', genre)

            except mysql.connector.Error as error:
                report('DB read fail', 'normalize_genre', str(error))
                print("Error reading data from MySQL table", str(error))

        if connection.is_connected():
                connection.close()
                cursor.close()

        return ', '.join(genres_list)

    except:
        return text