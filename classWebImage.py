"""Classes and functions for downloading images from websites and image hosters"""
import os
import shutil

import requests
import shortuuid
from bs4 import BeautifulSoup

from config import ENABLE_UNITS, IMG_PATH
from reportMaster import report
from support import get_page

# Image hosters and subclass names for downloading images
IMAGE_HOSTERS = [
    {'url': 'fastpic.org', 'className': 'FastpicOrg'},
    {'url': 'imageban.ru', 'className': 'ImagebanRu'},
]

class WebImage():
    """Parent class, can download image from direct URL"""
    def __init__(self, url):
        self.url = url

    def download(self):
        # Get file extension
        url = delete_url_options(self.url)
        extension = url[url.rfind('.'):]
        
        # Generate filename
        filename = shortuuid.uuid() + extension

        # Check if file exist
        while os.path.isfile(IMG_PATH + filename):
            filename = shortuuid.uuid() + extension
        
        # Download and save image
        headers = {
            'User-Agent' : 'Mozilla/5.0',
        }
        image = requests.get(self.url, headers=headers, stream=True)

        if image.status_code == 200:
            if ENABLE_UNITS['images']:
                with open(IMG_PATH + filename, 'wb') as file:
                    image.raw.decode_content = True
                    shutil.copyfileobj(image.raw, file)
            else:
                print('Simulate download ' + self.url + ' -> ' + filename)
                return ''
        else:
            # Report error
            report('Image 404', self.__class__.__name__, self.url)
            return ''

        return filename

class ImagebanRu(WebImage):
    def __init__(self, url):
        self.url = BeautifulSoup(get_page(url), 'html.parser').find(id='img_main')['src']
        
class FastpicOrg(WebImage):
    def __init__(self, url):
        self.url = BeautifulSoup(get_page(url), 'html.parser').find(class_='image img-fluid')['src']

# Download image and return filename
def download_image(url):
    
    # Delete URL options
    clear_URL = delete_url_options(url)

    # Find and create image hoster object
    for imgHoster in IMAGE_HOSTERS:
        if imgHoster['url'] in url:
            imgClass = globals()[imgHoster['className']]
            image = imgClass(url)
            break
    else:
        # Check if it's direct link
        if clear_URL[clear_URL.rfind('.'):].lower() in ['.jpg', '.jpeg', '.png']:
            image = WebImage(url)
        else:
            # Report error
            report('No crawler for image', 'download_image', url)
            return False

    # Download image and return filename
    return image.download()

# Delete URL options after '?' and '#'
def delete_url_options(url):
    if url.rfind('?') > 0:
        url = url[:url.rfind('?')]
    if url.rfind('#') > 0:
        url = url[:url.rfind('#')]
    return url