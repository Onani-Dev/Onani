import re

import requests
from termcolor import colored

import system.values
from system.engine import log_exception

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
home_page = "http://rule34.paheal.net/"
regex = ["https:\/\/[a-zA-Z0-9]{1,}\.paheal\.net\/_images\/[a-zA-Z0-9]{1,}\/[a-zA-Z0-9._%'\\-]{1,}"]


def scrape(query):
    page = 0
    while system.values.scraping:
        page += 1
        try:
            src = s.get(
                f"http://rule34.paheal.net/post/list/{query}/{page}", headers=headers, timeout=60)
        except Exception as e:
            log_exception(e)
            continue
        if not system.values.scraping:
            break
        else:
            for r in regex:
                reg = re.findall(r, str(src.text))
                for r in reg:
                    img = {
                        "file_url": r,
                        "sources": [r],
                        "tags": [query],
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
    system.values.shutdown_count -= 1
