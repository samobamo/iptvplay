#! /usr/bin/python3
import urllib.request
import gzip
import shutil
import smtplib
import re
import os
import datetime
from pathlib import Path
from email.mime.text import MIMEText

# Constants
EPG_URL = 'http://freeweb.t-2.net/itak/epg_b.xml.gz'
PLAYLIST_URL = 'http://freeweb.t-2.net/itak/T2_HD.m3u'
STORAGE_PATH = Path('/storage/tvschedule')
EPG_GZ_PATH = Path('/tmp/epg.gz')
EPG_XML_PATH = STORAGE_PATH / 'epg.xml'
PLAYLIST_PATH = Path('playlist_hd.m3u')
ENV_FILE = Path('/storage/configs/.env')  # Securely store credentials here

# Email Configuration (loaded from .env)
EMAIL_USER = None
EMAIL_PASS = None
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_TO = None

def load_env(env_path=ENV_FILE):
    #Manually loads key-value pairs from an .env file.
    global EMAIL_USER, EMAIL_PASS, EMAIL_TO
    if not env_path.exists():
        print(f"Warning: {env_path} file not found. Skipping email setup.")
        return

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            if "=" in line and not line.startswith("#"):  # Ignore comments
                key, value = line.strip().split("=", 1)
                os.environ[key] = value  # Store as environment variable

    # Load email credentials
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    EMAIL_TO = os.getenv("EMAIL_TO")

def download_file(url: str, dest: Path):
    #Download a file from a given URL to a specified path.
    try:
        with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        print(f"Downloaded {url} -> {dest}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def extract_gzip(gz_path: Path, output_path: Path):
    #Extract a GZ file and save it to a specific location.
    try:
        with gzip.open(gz_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        gz_path.unlink()  # Delete GZ file after extraction
        print(f"Extracted {gz_path} -> {output_path}")
        return True
    except Exception as e:
        print(f"Error extracting {gz_path}: {e}")
        return False

def inplace_replace(filename: Path, old_string: str, new_string: str):
    #Replace occurrences of old_string with new_string in a file.
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            filedata = file.read()

        filedata = filedata.replace(old_string, new_string)

        with open(filename, 'w', encoding='utf-8') as file:
            file.write(filedata)

        print(f"Replaced '{old_string}' with '{new_string}' in {filename}")
        return True
    except Exception as e:
        print(f"Error modifying {filename}: {e}")
        return False

def compare_files():
    #Compare old and new playlists and count URL changes.
    old_file = STORAGE_PATH / 'playlist_hd.m3u'
    new_file = PLAYLIST_PATH

    old_count = sum(1 for _ in open(old_file, encoding='utf-8') if 'http:' in _)
    new_count = sum(1 for _ in open(new_file, encoding='utf-8') if 'http:' in _)

    return old_count, new_count

def send_status_mail(lines_old, lines_new):
    #Send an email with the number of channels added/removed.
    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials are missing. Skipping email notification.")
        return

    try:
        change = lines_new - lines_old
        today = datetime.date.today().strftime('%b %d %Y')

        if change > 0:
            body_msg = f'{change} channels have been added'
        elif change < 0:
            body_msg = f'{-change} channels have been removed'
        else:
            body_msg = 'No channels have been added or removed'

        msg = MIMEText(body_msg)
        msg['Subject'] = f'Channel list updated on {today}'
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_TO

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.sendmail(EMAIL_USER, [EMAIL_TO], msg.as_string())

        print("Status email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

def download_epg_and_playlist():
    #Download EPG and playlist, process files, and send updates.
    if download_file(EPG_URL, EPG_GZ_PATH):
        extract_gzip(EPG_GZ_PATH, EPG_XML_PATH)

    if download_file(PLAYLIST_URL, PLAYLIST_PATH):
        inplace_replace(PLAYLIST_PATH, 'udp://@', 'http://192.168.1.1:1234/udp/')

        # Compare new and old playlist counts
        lines_old, lines_new = compare_files()
        shutil.move(PLAYLIST_PATH, STORAGE_PATH / PLAYLIST_PATH.name)

        print(f"Channels before: {lines_old}, Channels after: {lines_new}")
        send_status_mail(lines_old, lines_new)

if __name__ == "__main__":
    load_env()  # Load email credentials before running the script
    download_epg_and_playlist()
