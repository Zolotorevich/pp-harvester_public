from datetime import datetime


def log(sender, type, message):
    # Get current date
    date = datetime.now()

    # Generate log entry
    entry = f"[{type}] [{date}] {sender}: {message}\n"

    # White logfile
    with open("log.txt", "a") as logfile:
        logfile.write(entry)