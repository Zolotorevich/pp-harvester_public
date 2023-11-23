import os
import pathlib
from datetime import datetime, timedelta

from config import IMG_PATH, MEDIA_EXPIRE_DAYS, VIDEO_PATH
from reportMaster import report

# Generate list of files
listOfFiles = [f for f in pathlib.Path(IMG_PATH).iterdir() if f.is_file()]
listOfFiles += [f for f in pathlib.Path(VIDEO_PATH).iterdir() if f.is_file()]
listOfFiles += [f for f in pathlib.Path(VIDEO_PATH + 'weekly/').iterdir() if f.is_file()]

# Calc expire date
expireDate = datetime.now() - timedelta(days=MEDIA_EXPIRE_DAYS)

# Delete old files
numberOfDeleted = 0
for file in listOfFiles:

    fileDate = datetime.fromtimestamp(os.path.getctime(file))

    if expireDate > fileDate:
        os.remove(file)
        numberOfDeleted += 1

# Report to human
if numberOfDeleted:
    report('Cleanup', 'Clean UP', str(numberOfDeleted))