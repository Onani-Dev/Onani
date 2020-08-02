import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.values
from system.engine import log_exception

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0"
home_page = "https://chan.sankakucomplex.com"
regex = []


def scrape(query):
    page = 1
    while system.values.scraping:
        try:
            src = s.get(f"https://capi-v2.sankakucomplex.com/posts", params={"page": page, "limit": 10, "tags": query}, timeout=60)
        except Exception as e:
            log_exception(e)
            continue
        if not system.values.scraping:
            break
        try:
            data = src.json()
        except Exception:
            continue
        else:
            page += 1
        for image in data:
            try:
                artist = "Unknown"
                copyrights = list()
                characters = list()
                tags = list()
                for tag in image['tags']:
                    if tag["type"] == 3:
                        copyrights.append(tag["name"])
                    elif tag["type"] == 4:
                        characters.append(tag["name"])
                    elif tag["type"] == 1:
                        artist = tag["name"]
                    else:
                        tags.append(tag["name"])
                img = {
                    "file_url": image["file_url"],
                    "sources": [f"https://chan.sankakucomplex.com/post/show/{image['id']}", image["source"], image["file_url"]],
                    "tags": tags,
                    "artist": artist,
                    "additional": {
                        "characters": characters,
                        "copyrights": copyrights
                    }
                }
                if img in system.values.found:
                    pass
                else:
                    if not system.new_print_style:
                        system.print_queue.append(
                            colored(img["file_url"], "green"))
                    system.values.found.append(img)
            except Exception as e:
                log_exception(e)
                continue
        time.sleep(5)
    system.values.shutdown_count -= 1

