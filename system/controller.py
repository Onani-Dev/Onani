import threading
import time

from colorama import init
from termcolor import colored

import system.download
import system.title
import system.values
from scrapers import (danbooru, e621, e_hentai, gelbooru, giantess_booru,
                      hypno_hub, konachan, realbooru, rule34, rule34_paheal,
                      sankaku_complex, twitter, xbooru, yandere, yiff)
from system.engine import *
from system.values import (downloaded, downloading, finished, found, scraping,
                           written)


def scrape_controller(query, max_downloads):
    threading.Thread(target=system.title.scraping_title, args=[query], daemon=True).start()
    system.values.scraping = True
    system.values.shutdown_count = 0
    threading.Thread(target=system.download.download_controller, args=[
        query, max_downloads], daemon=True).start()
    if query == "None":
        query = ""
    threading.Thread(target=danbooru.scrape, args=[query], daemon=True).start()
    threading.Thread(target=e621.scrape, args=[query], daemon=True).start()
    threading.Thread(target=gelbooru.scrape, args=[query], daemon=True).start()
    threading.Thread(target=giantess_booru.scrape, args=[query], daemon=True).start()
    threading.Thread(target=hypno_hub.scrape, args=[query], daemon=True).start()
    threading.Thread(target=konachan.scrape, args=[query], daemon=True).start()
    threading.Thread(target=realbooru.scrape, args=[query], daemon=True).start()
    # threading.Thread(target=rule34_paheal.scrape, args=[query], daemon=True).start()
    threading.Thread(target=rule34.scrape, args=[query], daemon=True).start()
    threading.Thread(target=sankaku_complex.scrape, args=[query], daemon=True).start()
    threading.Thread(target=xbooru.scrape, args=[query], daemon=True).start()
    threading.Thread(target=yandere.scrape, args=[query], daemon=True).start()
    system.values.shutdown_count += 11


def custom_scrape_controller(query, max_downloads):
    threading.Thread(target=system.title.scraping_title, args=[query], daemon=True).start()
    system.values.scraping = True
    system.values.shutdown_count = 0
    threading.Thread(target=system.download.download_controller, args=[
        query, max_downloads], daemon=True).start()
    if query == "None":
        query = ""
    if system.values.custom_dict['DanBooru']:
        threading.Thread(target=danbooru.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['e621']:
        threading.Thread(target=e621.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['GelBooru']:
        threading.Thread(target=gelbooru.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['Giantess Booru']:
        threading.Thread(target=giantess_booru.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['HypnoHub']:
        threading.Thread(target=hypno_hub.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['KonaChan']:
        threading.Thread(target=konachan.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['RealBooru']:
        threading.Thread(target=realbooru.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    # if system.values.custom_dict['Rule 34 Paheal']:
    #     threading.Thread(target=rule34_paheal.scrape, args=[query], daemon=True).start()
    #     system.values.shutdown_count += 1
    if system.values.custom_dict['Rule 34']:
        threading.Thread(target=rule34.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['Sankaku Complex']:
        threading.Thread(target=sankaku_complex.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1
    if system.values.custom_dict['XBooru']:
        threading.Thread(target=xbooru.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1 
    if system.values.custom_dict['Yande.re']:
        threading.Thread(target=yandere.scrape, args=[query], daemon=True).start()
        system.values.shutdown_count += 1


def ehentai_scrape_controller(query):
    webpage = e_hentai.parse_name(query)
    threading.Thread(target=system.download.download_controller, args=[
                     query, system.scraper_threadcount]).start()
    threading.Thread(target=e_hentai.scrape, args=[query]).start()
    system.values.shutdown_count += 1


def twitter_scrape_controller(query):
    threading.Thread(target=system.download.download_controller, args=[
                     query, system.scraper_threadcount]).start()
    threading.Thread(target=system.title.twitter_title, args=[query]).start()
    threading.Thread(target=twitter.scrape, args=[query]).start()
    system.values.shutdown_count += 1


def yiff_scrape_controller(query, threads):
    threading.Thread(target=system.download.download_controller, args=[
                     query, threads]).start()
    threading.Thread(target=system.title.e_hentai_title, args=[query]).start()
    threading.Thread(target=yiff.scrape, args=[query]).start()
    system.values.shutdown_count += 1


def boorumation_controller():
    threading.Thread(target=system.title.scraping_title,
                     args=["BooruMation"], daemon=True).start()
    threading.Thread(target=system.download.download_controller, args=[
                     "None", system.scraper_threadcount]).start()
    threading.Thread(target=danbooru.boorumation, daemon=True).start()
    system.values.shutdown_count += 1


def stop_scraping(passive=False):
    i = input("")
    if i.lower() == "force":
        system.values.scraping = False
        pass
    else:
        stoptime = time.time()
        if not passive:
            system.values.scraping = False
        system.values.pause_pq = True
        clear()
        while system.values.shutdown_count > 0:
            print(f"Shutting down threads, Please wait... ({system.values.shutdown_count} remaining.)")
            print(f"Downloads: [{system.values.finished}/{len(system.values.downloaded)} images downloaded | {system.values.downloading} running downloader threads.]")
            time.sleep(0.5)
            clear()
            if int(time.time() - stoptime) > 300 and system.values.downloading < 5:
                print("taking too long")
                break
        while system.values.downloading > 0:
            print(f"Finishing up downloads, Please wait...")
            print(f"Downloads: [{system.values.finished}/{len(system.values.downloaded)} images downloaded | {system.values.downloading} running downloader threads.]")
            time.sleep(0.5)
            clear()
            if int(time.time() - stoptime) > 300 and system.values.downloading < 5:
                print("taking too long")
                break
        system.values.pause_pq = False
        while len(system.print_queue) != 0:
            time.sleep(3)
