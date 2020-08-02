import re
import urllib.parse

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.values
from system.engine import log_exception

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}

home_page = "https://realbooru.com/"
regex = []


def scrape(query):
    s = requests.Session()
    page = 1
    while system.values.scraping:
        try:
            src = s.get("https://realbooru.com/index.php", params={"page": "dapi", "s": "post", "q": "index", "json": 1, "tags": query, "pid": page}, timeout=60)
        except Exception as e:
            log_exception(e)
            continue
        if not system.values.scraping:
            break
        try:
            data = src.json()
        except Exception as e:
            continue
        else:
            page += 1
        for image in data:
            try:
                img = {
                    "file_url": f'{home_page}images/{image["directory"]}/{image["image"]}',
                    "sources": [f"https://realbooru.com/index.php?page=post&s=view&id={image['id']}", f'{home_page}images/{image["directory"]}/{image["image"]}'],
                    "tags": image["tags"].split(" "),
                    "artist": image["owner"],
                    "additional": {}
                }
                if img in system.values.found:
                    pass
                else:
                    if not system.new_print_style:
                        system.print_queue.append(colored(img["file_url"], "green"))
                    system.values.found.append(img)
            except:
                continue
    system.values.shutdown_count -= 1
