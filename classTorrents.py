"""Classes for fetching torrents list and items"""

from datetime import datetime

import mysql.connector
from bs4 import BeautifulSoup

import support
from classWebImage import download_image
from config import DB_OPTIONS, ENABLE_UNITS, TRACKERS
from reportMaster import report


class Torrents():
    """Global class for torrents"""

    def __init__(self):
        # Get list of torrents, like [{'name':'name', 'url':'url'}]
        list_of_torrents = self.parse_torrents_titles_and_links()
        if not list_of_torrents:
            return

        # Remove torrents, that already in DB
        list_of_torrents = self.remove_existing_torrents(list_of_torrents)
        if not list_of_torrents:
            return

        # Parse individual torrents
        torrents_data = []
        for item in list_of_torrents:
            # Parse data
            data = self.parse_torrent_data(item)

            # White to DB
            if data:
                # Append info for log
                torrents_data.append(data)

                # Connect to db
                if ENABLE_UNITS['dbWrite']:
                    try:
                        connection = mysql.connector.connect(**DB_OPTIONS)
                        cursor = connection.cursor()
                        cursor.execute(self.query, data)
                        connection.commit()
                        cursor.close()

                    except mysql.connector.Error as error:
                        report('DB write fail',
                               self.__class__.__name__,
                               str(error) + ' ' + data[2] + ' ' + data[3])
                        print("Failed to insert record into table {}".format(error))

                    finally:
                        if connection.is_connected():
                            connection.close()
                            
                else:
                    print('Simulated write to DB')

        # Print results
        if torrents_data:
            report('Complete', self.__class__.__name__, str(len(list_of_torrents)))
            print('\n\n***RESULTS***\n')
            for item in torrents_data:
                print('\n\n\n========================\n')
                print('\n—\n'.join([str(i) for i in item]))
        else:
            report('No torrents parsed', self.__class__.__name__, str(len(list_of_torrents)))

class GamesTorrents(Torrents):
    """Global class for games torrents"""

    query = 'INSERT INTO games_games VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    
    # Check game in DB
    def remove_existing_torrents(self, list_of_torrents):

        # Get existing rawTitles from DB
        query = 'SELECT rawTitle FROM games_games WHERE rawTitle IN ('
        for item in list_of_torrents:
            query += '"' + item['rawTitle'] + '",'
        query = query[:-1] + ')'

        # Exicute query
        try:
            connection = mysql.connector.connect(**DB_OPTIONS)
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()

        except mysql.connector.Error as error:
            report('DB read fail', self.__class__.__name__, str(error))
            print("Error reading data from MySQL table", str(error))
        finally:
            if connection.is_connected():
                connection.close()
                cursor.close()

        # Generate list for serach
        titles_in_DB = []
        for item in result:
            titles_in_DB.append(item[0])

        # Delete existed in DB from list
        for title in titles_in_DB:
            for torrent in list_of_torrents:
                if torrent['rawTitle'] == title:
                    list_of_torrents.remove(torrent)
                    break
        
        # Check if no new torrents
        if not list_of_torrents:
            report('No new torrents', self.__class__.__name__)
            return False

        return list_of_torrents


class RuTrackerGames(GamesTorrents):
    """Class for rutracker games"""

    def parse_torrents_titles_and_links(self):
        
        # Request HTML
        html = support.get_page(TRACKERS['rutracker_games'], 'Windows-1251')

        # Check if html empty and send report
        if not html:
            report('Torrents list 404', self.__class__.__name__)
            return False

        # Get titles and links from HTML
        soup = BeautifulSoup(html, 'html.parser')
        title_container = soup.find_all('a', class_="torTopic")

        # Chech if BS can't find any
        if not title_container:
            report('Torrents list parse error', self.__class__.__name__)
            return False

        # Store raw titles and links
        torrents = []
        for item in title_container:
            title = item.text[:item.text.find('[') - 1]

            # Check if title alredy in list
            if not any(i['rawTitle'] == title for i in torrents):
                torrents.append({
                    'url' : 'https://rutracker.org/forum/' + item.get('href'),
                    'rawTitle' : title})

        return torrents

    def parse_torrent_data(self, torrent):
        
        # Request HTML
        html = support.get_page(torrent['url'], 'Windows-1251')

        # Check if html empty and send report
        if not html:
            report(
                'Torrent page 404',
                self.__class__.__name__,
                torrent['rawTitle'] + ' ' + torrent['url'])
            return False

        # Parse data
        soup = BeautifulSoup(html, 'html.parser')

        # Get all text on page
        raw_page_text = soup.find('div', class_='post_wrap').text
        raw_page_text = support.optimize_raw_text('rutracker', raw_page_text)

        # Description
        description = support.find_value(raw_page_text, 'описание', removePunctuation=False)

        # Genres
        genre = support.find_value(raw_page_text, 'жанр: ')

        # System requirements
        sys_CPU = support.find_value(raw_page_text, 'Процессор: ')    
        sys_GPU = support.find_value(raw_page_text, 'Видеокарта: ')
        sys_RAM = support.find_value(raw_page_text, 'Память: ')

        # Replace '/' with comma
        sys_GPU = support.remove_trash_symbols(sys_GPU)
        sys_CPU = support.remove_trash_symbols(sys_CPU)

        # Get rating
        rating = support.metacritic_score('game', torrent['rawTitle'])

        # Find screenshots
        screenshots_URLs = []
        screens_titles = ['Скриншоты:', 'Скриншоты', 'СКРИНШОТЫ', 'Screenshots']
        screens_titles_stopwords = ['Скриншоты инсталлятора',]

        # Find screenshots container (foldable div)
        screens_containers = soup.find_all('div', class_='sp-head folded', string=screens_titles)
        
        for container in screens_containers:

            # Check for stop-names
            if container.text not in screens_titles_stopwords:

                # Look inside container
                img_container = container.findNext('div', class_='sp-body'
                                                ).find_all('a', class_='postLink')

                # Save img URLs
                for link in img_container:
                    # Save max 10 screens
                    if len(screenshots_URLs) <= 10:
                        screenshots_URLs.append(link.get('href'))
                    else:
                        break

        # Download screenshots
        screenshots_filenames = []
        if screenshots_URLs:
            for url in screenshots_URLs:
                newImage = download_image(url)
                if newImage:
                    screenshots_filenames.append(newImage)

        else:
            report('No torrent screenshots',
                   self.__class__.__name__,
                   torrent['rawTitle'] + ' ' + torrent['url'])
        
        # Download video and get filename
        youtube_video = support.download_video(torrent['rawTitle'] + ' game trailer')

        # Check if video not downloaded
        if not youtube_video:
            youtube_video = {'url': '', 'filename': ''}

        # Return SQL-friendly
        # ID
        # url
        # rawTitle
        # rawText
        # title
        # description
        # genre
        # sysCPU
        # sysGPU
        # sysRAM
        # ratingCritics
        # ratingUsers
        # screenshotsFilenames
        # screenshotsSelected
        # videoURL
        # videoFilename
        # status
        # date
        return (
                None,
                torrent['url'],
                torrent['rawTitle'],
                raw_page_text.strip(),
                torrent['rawTitle'],
                description.strip(),
                support.normalize_genre(genre),
                sys_CPU,
                sys_GPU,
                sys_RAM,
                rating['critics'],
                rating['users'],
                ','.join(screenshots_filenames),
                ','.join(screenshots_filenames[:3]),
                youtube_video['url'],
                youtube_video['filename'],
                'await',
                datetime.now()
            )