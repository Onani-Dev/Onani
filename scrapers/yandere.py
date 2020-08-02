import re
import urllib.parse

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.values
from system.engine import log_exception

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
home_page = "https://yande.re"
regex = []


def scrape(query):
    page = 0
    discovered = list()
    while system.values.scraping:
        page += 1
        try:
            src = s.get("https://yande.re/post.json", params={"tags": query, "page": page, "limit": 100}, timeout=60)
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
            img = {
                "file_url": image["file_url"],
                "sources": [f"https://yande.re/post/show/{image['id']}/", image["source"], image["file_url"]],
                "tags": image["tags"].split(" "),
                "artist": "Unknown",
                "additional": {}
            }
            if img in system.values.found:
                pass
            else:
                if not system.new_print_style:
                    system.print_queue.append(colored(img["file_url"], "green"))
                system.values.found.append(img)
    system.values.shutdown_count -= 1
