import re
import sys
import threading
import time

import requests
from bs4 import BeautifulSoup
from termcolor import colored

import system.download
import system.title
import system.values
from system.engine import log_exception

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
s = requests.Session()


def login(user, passw):
    if system.values.ehentai_cookies is not None:
        print("Using cached session.")
        s.cookies = system.values.ehentai_cookies
        return True
    else:
        print(f"Logging into: {system.ehentai_username}, Please wait...")
        src = s.post("https://forums.e-hentai.org/index.php",
                    params={'act': 'Login', 'CODE': '01'}, data={'CookieDate': '1', 'b': 'd', 'bt': '1-1', 'UserName': user, 'PassWord': passw, 'ipb_login_submit': 'Login!'}, headers=headers)
        if src.status_code == 200:
            system.values.ehentai_cookies = s.cookies
            return True
        else:
            return False


def check_limits():
    is_loggedin = login(system.ehentai_username, system.ehentai_password)
    if not is_loggedin:
        print("Login Failure.")
    else:
        print("Login success!")
        try:
            src = s.get("https://e-hentai.org/home.php").text
            soup = BeautifulSoup(src, "lxml")
            box = soup.find("div", class_="homebox")
            numbers = box.findAll("strong")
            t = list()
            for number in numbers:
                t.append(int(number.text))
            numbers = tuple(t)
            print(f"Limit: {numbers[0]}/{numbers[1]}\nRecharge rate of {numbers[2]} per minute.\nReset cost: {numbers[3]} Credits")
        except:
            print("Error getting limits.")


def return_tags(html):
    processed = set()
    artist = set()
    tags = re.findall(
        "https:\/\/e-hentai\.org\/tag\/[a-zA-Z0-9]{1,}\:[a-zA-Z0-9+]{1,}", html)
    for tag in tags:
        if tag.split("/")[-1].startswith("artist:"):
            artist.add(tag.split(":")[-1].replace("+", "_"))
        processed.add(tag.split(":")[-1].replace("+", " "))
    if len(artist) == 0:
        artist.add("Unknown")
    return (list(processed), list(artist)[0])


def parse_name(gallery):
    src = s.get(gallery + "?nw=always", headers=headers)
    try:
        soup = BeautifulSoup(src.text, 'lxml')
        title = soup.title.text.replace(" - E-Hentai Galleries", "")
    except Exception:
        return None, None
    else:
        return title, src.text


def scrape(link):
    found_pics = list()
    count = 0
    if system.ehentai_username is not None and system.ehentai_password is not None:
        is_loggedin = login(system.ehentai_username, system.ehentai_password)
        if is_loggedin:
            print("Login success! Onani will now be able download higher quality images.")
        else:
            print("Login Failure. Onani will only be able to download lower resolution images.")
    else:
        is_loggedin = False
    try:
        title, src = parse_name(link)
        if title[0] is None:
            raise Exception("Error Parsing Link.")
        else:
            threading.Thread(target=system.title.e_hentai_title, args=[title]).start()
            pages = re.findall("https:\/\/e-hentai\.org\/g\/[0-9]{1,}\/[0-9a-zA-Z]{1,}\/\?p=[0-9]{1,}", src)
            for page in pages:
                if int(page.replace(f"{link}?p=", "")) > count:
                    count = int(page.replace(f"{link}?p=", ""))
            count += 1
            if count < 2:
                logic = ""
            else:
                logic = "s"
            print(colored(f"Gallery has {count} page{logic}.", "red"))
            print(f"{colored('Downloading:','red')} {colored(title, 'blue')}{colored(', please wait.','red')}")
    except Exception as e:
        log_exception(e)
    else:
        for x in range(count):
            if not system.new_print_style:
                system.print_queue.append(f'{link}?p={x}')
            try:
                page = s.get(f'{link}?p={x}', headers=headers)
            except Exception as e:
                log_exception(e)
            reg = re.findall("https:\/\/e-hentai\.org\/s\/[0-9a-zA-Z]{1,}\/[0-9-]{1,}", str(page.text))
            for r in reg:
                if r in found_pics:
                    continue
                else:
                    found_pics.append(r)
                src = s.get(r, headers=headers)
                if is_loggedin:
                    reg = re.findall("https:\/\/e-hentai\.org\/fullimg\.php\?gid=[\d]{1,}&page=[\d]{1,}&key=[\w\d]{1,}", str(src.text).replace("&amp;", "&"))
                    if len(reg) == 0:
                        reg = re.findall("[0-9a-zA-Z_;:.-\/]{1,}\/h\/[a-zA-Z0-9%._-]{1,}\/keystamp=[a-zA-Z0-9%._-]{1,};fileindex=[a-zA-Z0-9]{1,};xres=[a-zA-Z0-9]{1,}/[a-zA-Z0-9._%=-]{1,}", str(src.text))
                else:
                    reg = re.findall("[0-9a-zA-Z_;:.-\/]{1,}\/h\/[a-zA-Z0-9%._-]{1,}\/keystamp=[a-zA-Z0-9%._-]{1,};fileindex=[a-zA-Z0-9]{1,};xres=[a-zA-Z0-9]{1,}/[a-zA-Z0-9._%=-]{1,}", str(src.text))
                for img in reg:
                    if is_loggedin:
                        src = s.get(img, headers=headers, allow_redirects=True, stream=True)
                        img = src.url.replace("?dl=1", "")
                    img = {
                        "file_url": img,
                        "sources": [link],
                        "tags": return_tags(page.text)[0] + [link, title],
                        "artist": return_tags(page.text)[1],
                        "additional": {}
                    }
                    if img in system.values.found:
                        pass
                    else:
                        if not system.new_print_style:
                            system.print_queue.append(colored(img, "green"))
                        system.values.found.append(img)
    while system.values.downloading > 0:
        time.sleep(1)
    system.values.shutdown_count -= 1
    system.values.scraping = False
