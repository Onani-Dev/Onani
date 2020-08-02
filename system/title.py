import ctypes
import random
import sys
import time
import urllib.parse

import system.values
from system.engine import *
from system.values import (downloaded, downloading,
                           finished, found, scraping, written)


def notification_alert():
    print(chr(7))


def change_title(text):
    if sys.platform.startswith('win32'):
        ctypes.windll.kernel32.SetConsoleTitleW(text)
    else:
        sys.stdout.write(f"\x1b]2;{text}\x07")
        sys.stdout.flush()


def change_title_animation(text, delay):
    add = str()
    if sys.platform.startswith('win32'):
        for char in text:
            add += char
            ctypes.windll.kernel32.SetConsoleTitleW(add)
            time.sleep(delay)
    else:
        for char in text:
            add += char
            sys.stdout.write(f"\x1b]2;{text}\x07")
            sys.stdout.flush()
            time.sleep(delay)


def scraping_title(query):
    while system.values.scraping:
        change_title(f"Onani {system.__version__} | [Query: {urllib.parse.unquote(query)}] [Downloaded: {system.values.finished}/{len(system.values.found)}] [Thread Status: {system.values.downloading} downloading]")
        time.sleep(0.1)
    while system.values.downloading > 0:
        change_title(f"Onani {system.__version__} | [Query: {urllib.parse.unquote(query)}] [Downloaded: {system.values.finished}/{len(system.values.downloaded)}] [Thread Status: {system.values.downloading} downloading]")
        time.sleep(0.1)
    notification_alert()
    change_title_animation(
        f"Onani {system.__version__} | Task finished!", 0.05)
    time.sleep(3)
    change_title_animation(f"Onani {system.__version__}", 0.2)


def downloader_title(filename):
    while len(system.values.found) > 0:
        change_title(
            f"Onani {system.__version__} | [File: {urllib.parse.unquote(filename)}] [Downloaded: {system.values.finished}/{len(system.values.found)}]")
        time.sleep(0.1)
    notification_alert()
    change_title_animation(
        f"Onani {system.__version__} | Task finished!", 0.05)
    time.sleep(3)
    change_title_animation(f"Onani {system.__version__}", 0.2)


def e_hentai_title(gallery):
    while system.values.scraping:
        change_title(
            f"Onani {system.__version__} | [Gallery: {gallery}] [Downloaded: {system.values.finished}/{len(system.values.found)}]")
        time.sleep(0.1)
    notification_alert()
    change_title_animation(
        f"Onani {system.__version__} | Task finished!", 0.05)
    time.sleep(3)
    change_title_animation(f"Onani {system.__version__}", 0.2)


def twitter_title(user):
    while system.values.scraping or system.values.downloading > 0:
        change_title(
            f"Onani | [User: {user}] [Downloaded: {system.values.finished}/{len(system.values.found)}] [Thread Status: {system.values.downloading} downloading]")
    notification_alert()
    change_title_animation(
        f"Onani {system.__version__} | Task finished!", 0.05)
    time.sleep(3)
    change_title_animation(f"Onani {system.__version__}", 0.2)


def startup_title():
    change_title_animation("Welcome to Onani!", 0.05)
    time.sleep(1.8)
    if random.randint(1, 10) == 5:
        change_title_animation(f"オナニー {system.__version__}", 0.05)
    else:
        change_title_animation(f"Onani {system.__version__}", 0.05)
