import re
import sys
import threading
import time

import html2text
import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.download
import system.title
import system.values
from system.engine import list_remove_empty, log_exception

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
regex = []


def get_page(link):
    processed = set()
    src = s.get(link)
    soup = BeautifulSoup(src.text, 'html.parser')
    name = soup.find("span", attrs={"class": "yp-info-name"})
    _id = link.split("/")[-1]
    small = name.find("small")
    if small is not None:
        small = small.text.replace("(", "").replace(")", "").lstrip()
    for span in soup.findAll('span', attrs={"class": "yp-cat-name"}):
        processed.add(span.text)
    for t in ['Furry', 'Pony', 'Human', 'Xeno', 'Other', 'Digital art', 'Traditional art', 'CGI', 'Animation', 'Games', 'Literature', 'Music', 'Cosplay', 'Crafts', 'Videos']:
        if t in processed:
            processed.remove(t)
    
    return (name, small), soup, _id, list(processed)


def scrape(link):
    found_pics = list()
    name, soup, _id, tags = get_page(link)
    src = s.get(f"https://yiff.party/{_id}.json")
    try:
        data = src.json()
    except Exception as e:
        pass
    else:
        for post in data["posts"]:
            for file_ in post["attachments"]:
                try:
                    img = {
                        "file_url": file_["file_url"],
                        "sources": [link, file_["file_url"]],
                        "tags": tags,
                        "artist": name[1],
                        "additional": {
                            "title": post['title'],
                            "description": html2text.html2text(post["body"])
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
            try:
                img = {
                    "file_url": post["post_file"]["file_url"],
                    "sources": [link, post["post_file"]["file_url"]],
                    "tags": tags,
                    "artist": name[1],
                    "additional": {
                        "title": post['title'],
                        "description": html2text.html2text(post["body"])
                    }
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
        for post in data["shared_files"]:
            try:
                img = {
                    "file_url": post["file_url"],
                    "sources": [link, post["file_url"]],
                    "tags": tags,
                    "artist": name[1],
                    "additional": {
                        "title": post['title'],
                        "description": post["description"]
                    }
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

    while system.values.downloading > 0:
        time.sleep(1)
    system.values.shutdown_count -= 1
    system.values.scraping = False
