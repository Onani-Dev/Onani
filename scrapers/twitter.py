import re
import time

import tweepy
from termcolor import colored

import system.values
from system.engine import log_exception


def parse_tweet(tweet, user):
    found_images = list()
    if not hasattr(tweet, 'retweeted_status'):
        try:
            tweet._json['extended_entities']['media']
        except:
            pass
        else:
            for media in tweet._json['extended_entities']['media']:
                if media['type'] == 'video':
                    biggest = [0, None]
                    for variant in media['video_info']['variants']:
                        try:
                            variant['bitrate']
                        except:
                            pass
                        else:
                            if variant['bitrate'] > biggest[0]:
                                biggest = [variant['bitrate'], variant['url']]
                    if not biggest[1] is None:
                        found_images.append(biggest[1].split("?")[0])
                elif media['type'] == 'photo':
                    found_images.append(media['media_url'].replace(".jpg", ".png"))
        for tweet_img in found_images:
            img = {
                "file_url": tweet_img,
                "sources": [f"https://twitter.com/{user}/"],
                    "tags": [user],
                    "artist": user,
                    "additional": {}
                }  
            if img in system.values.found:
                pass
            else:
                if not system.new_print_style:
                    system.print_queue.append(
                        colored(img["file_url"], "green"))
                system.values.found.append(img)


def scrape(user):
    auth = tweepy.AppAuthHandler(
        "UoXn7coZdwbtSy0MHvUug", "oFO5PW3j3oKAMqThgKzEg8Jlejmu4siGCrkPSMfo")
    api = tweepy.API(auth)
    found_tweets = list()
    try:
        new_tweets = api.user_timeline(
            screen_name=user, count=1, tweet_mode='extended')
        found_tweets.extend(new_tweets)
        oldest = found_tweets[-1].id - 1
        parse_tweet(new_tweets[0], user)
    except Exception as e:
        log_exception(e)
    else:
        while len(new_tweets) > 0:
            try:
                new_tweets = api.user_timeline(
                    screen_name=user, count=200, max_id=oldest, tweet_mode='extended')
                found_tweets.extend(new_tweets)
                oldest = found_tweets[-1].id - 1
                for tweet in new_tweets:
                    parse_tweet(tweet, user)
            except:
                pass
    system.values.shutdown_count -= 1
    system.values.scraping = False




# Old Method; Keeping here as backup in case this shit ever breaks
# 
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
# def scrape(user):
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     driver = webdriver.Chrome(chrome_options=chrome_options, executable_path="system/chromedriver")
#     driver.get(f"https://twitter.com/{user}/media")
#     last = list()
#     break_count = 0
#     while True:
#         if break_count == 5:
#             break
#         html = driver.find_element_by_tag_name('html')
#         for _ in range(5):
#             html.send_keys(Keys.END)
#             time.sleep(0.5)
#         links = re.findall("https:\/\/pbs\.twimg\.com\/media\/[a-zA-Z0-9]{15,}", driver.page_source)
#         for link in links:
#             if link + ".png" in system.values.found:
#                 continue
#             else:
#                 system.print_queue.append(colored(link + ".png", "green"))
#                 system.values.found.append(link + ".png")
#         if last == links:
#             break_count += 1
#         else:
#             if not break_count == 0:
#                 break_count -= 1
#             last = links
#     system.values.scraping = False
#     driver.close()



