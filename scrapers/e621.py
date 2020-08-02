import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.values
from system.engine import log_exception, plural_logic

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
home_page = "https://e621.net/"
regex = []


def scrape(query):
    page = 1
    while system.values.scraping:
        try:
            src = s.get("https://e621.net/posts.json", params={"tags": query, "page": page, "limit": 100}, timeout=60)
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
        for post in data['posts']:
            try:
                tags = list()
                for x in post['tags']:
                    tags.extend(post['tags'][x])
                try:
                    artist = post['tags']['artist'][0]
                except:
                    artist = "Unknown"
                sources = [f"https://e621.net/posts/{post['id']}", post['file']["url"]]
                try:
                    sources.extend(post['sources'])
                except:
                    pass
                img = {
                    "file_url": post['file']["url"],
                    "sources": sources,
                    "tags": tags,
                    "artist": artist,
                    "additional": {
                        "characters": post['tags']['character'],
                        "copyrights": post['tags']['copyright']
                    }
                }
                if img in system.values.found:
                    pass
                else:
                    if not system.new_print_style:
                        system.print_queue.append(colored(img, "green"))
                    system.values.found.append(img)
            except Exception:
                continue
    system.values.shutdown_count -= 1
