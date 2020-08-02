import re
import urllib.parse

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.values
from system.engine import log_exception

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
home_page = "https://giantessbooru.com"
regex = [
    "\/_images\/[a-zA-Z0-9]{1,}\/[a-zA-Z0-9._-]{1,}"]


def get_tags(soup):
    tags = list()
    alltag = soup.find_all("a", class_="tag_name")
    for tag in alltag:
        tag = urllib.parse.unquote(tag["href"].split("/")[-2])
        tags.append(tag)
    return tags


def scrape(query):
    page = 0
    cookies_jar = requests.cookies.RequestsCookieJar()
    cookies_jar.set('agreed', 'true')
    cookies_jar.set('ShowFurryContent', 'true')
    while system.values.scraping:
        page += 1
        try:
            src = s.get(
                f"https://giantessbooru.com/post/list/{query}/{page}", timeout=60, cookies=cookies_jar)
        except Exception as e:
            log_exception(e)
            continue
        if not system.values.scraping:
            break
        reg = re.findall("\/post\/view\/[0-9]{1,}", str(src.text))
        for r in reg:
            if not system.new_print_style:
                system.print_queue.append(home_page + r)
            try:
                src = s.get(home_page + r, timeout=60, cookies=cookies_jar)
            except Exception as e:
                log_exception(e)
                continue
            if not system.values.scraping:
                break
            else:
                source = home_page + r
                soup = BeautifulSoup(src.text, "lxml")
                for r in regex:
                    all = re.findall(r, src.text)
                    for img in all:
                        img = home_page + img
                        try:
                            img = {
                                "file_url": img,
                                "sources": [source, img],
                                "tags": get_tags(soup),
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
