import re

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.values
from system.engine import log_exception

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
home_page = "https://hypnohub.net"
regex = []

def scrape(query):
    page = 0
    while system.values.scraping:
        try:
            src = s.get("https://hypnohub.net/post/index.json", params={"tags": query, "page": page, "limit": 100}, timeout=60)
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
                img = {
                    "file_url": image["file_url"],
                    "sources": [f"https://hypnohub.net/post/show/{image['id']}/", image["source"], image["file_url"]],
                    "tags": image["tags"].split(" "),
                    "artist": "Unknown",
                    "additional": {}
                }
                if img in system.values.found:
                    pass
                else:
                    if not system.new_print_style:
                        system.print_queue.append(
                            colored(img["file_url"], "green"))
                    system.values.found.append(img)
            except:
                continue
    system.values.shutdown_count -= 1
