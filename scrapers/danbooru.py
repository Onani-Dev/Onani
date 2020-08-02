import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.values
from system.engine import plural_logic, log_exception

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
home_page = "https://danbooru.donmai.us"
regex = []


def scrape(query):
    page = 1
    while system.values.scraping:
        try:
            src = s.get("https://danbooru.donmai.us/posts.json", params={"tags": query, "page": page, "limit": 100}, timeout=60)
        except Exception as e:
            log_exception(e)
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
                    "sources": [f"https://danbooru.donmai.us/posts/{image['id']}", image["source"], image["file_url"]],
                    "tags": image["tag_string"].split(" "),
                    "artist": image["tag_string_artist"],
                    "additional": {
                        "characters": image["tag_string_character"].split(" "),
                        "copyrights": image["tag_string_copyright"].split(" ")
                    }
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


def boorumation():
    while system.values.scraping:
        new_posts = 0
        try:
             src = s.get("https://danbooru.donmai.us/posts.json", params={"limit": 100}, timeout=60)
        except Exception as e:
            log_exception(e)
            continue
        try:
            data = src.json()
        except Exception:
            continue
        for image in data:
            try:
                img = {
                    "file_url": image["file_url"],
                    "sources": [f"https://danbooru.donmai.us/posts/{image['id']}", image["source"], image["file_url"]],
                    "tags": image["tag_string"].split(" "),
                    "artist": image["tag_string_artist"],
                    "additional": {
                        "characters": image["tag_string_character"].split(" "),
                        "copyrights": image["tag_string_copyright"].split(" ")
                    }
                }
                if img in system.values.found:
                    pass
                else:
                    if not system.new_print_style:
                        system.print_queue.append(colored(img["file_url"], "green"))
                    system.values.found.append(img)
                    new_posts += 1
            except:
                continue
        if system.values.scraping:
            while len(system.print_queue) != 0:
                time.sleep(5)
            system.print_queue.append(f"Found {colored(new_posts, 'green')} new post{plural_logic(new_posts)}.\nWaiting for 120 seconds.")
            while len(system.print_queue) != 0:
                time.sleep(3)
            for x in range(120):
                if not system.values.scraping:
                    break
                print(f"\r{x + 1}", end="")
                time.sleep(1)
            print()
    system.values.shutdown_count -= 1
