import hashlib
import inspect
import io
import json
import os
import random
import re
import string
import sys
import threading
import time
import urllib.parse
import uuid
from binascii import hexlify
from datetime import datetime

import tracebackturbo as traceback
from playsound import playsound
from pypresence import Presence
from saucenao import SauceNao

import system.database
import system.download
import system.values
from system.values import *


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)
        system.values.vir_con.append(message)

    def flush(self):
        pass


def clear():
	system.values.vir_con = list()
	return os.system(('cls' if sys.platform.startswith('win32') else 'clear'))


def new_query(text):
	if text == "":
		text = str(None)
	return urllib.parse.quote(text)


def _any(lst):
    for elm in lst:
        if elm:
            return True
    return False


def startup():
	try:
		if not system.has_sinned:
			playsound("system/audio/startup.mp3")
		else:
			playsound("system/audio/sta.mp3")
	except:
		pass


def log_exception(e):
	if not os.path.isdir(f"{system.dirs.user_log_dir}/tracebacks"):
		os.mkdir(f"{system.dirs.user_log_dir}/tracebacks")
	curframe = inspect.currentframe()
	calframe = inspect.getouterframes(curframe, 2)
	with open(f"{system.dirs.user_log_dir}/tracebacks/traceback-{calframe[1][3]}-{int(time.time())}.txt", "w") as f:
		f.write(''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))


def create_api_key():
	return hexlify(os.urandom(20)).decode()


def make_safe_filename(s):
	def safe_char(c):
		if c.isalnum():
			return c
		else:
			return "_"
	return "".join(safe_char(c) for c in s).strip("_")


def print_thread():
	while True:
		if system.values.pause_pq:
			try:
				string = system.print_queue.pop()
			except:
				time.sleep(0.5)
			else:
				pass
		else:
			try:
				string = system.print_queue.pop()
			except:
				time.sleep(0.5)
			else:
				print(string)


def logger_thread():
	while True:
		string = system.logger_queue.get()
		if string is None:
			pass
		else:
			with open(f"{system.dirs.user_log_dir}/download_log.txt", "a") as f:
				f.write(f"{string}\n")
			system.logger_queue.task_done()


def get_md5(file, bytesio=False):
	hash_md5 = hashlib.md5()
	if not bytesio:
		with open(file, 'rb') as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash_md5.update(chunk)
	else:
		with file as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash_md5.update(chunk)
	return hash_md5.hexdigest()


def uniquify(path):
	filename, extension = os.path.splitext(path)
	counter = 0

	while os.path.exists(path):
		path = f"{filename}_{str(counter)}{extension}"
		counter += 1

	return path


def opposite_bool(x):
	return (False if x else True)


def presence_rank(count):
	if count < 100:
		return "Pathetic"
	elif count > 100 and count < 500:
		return "Casual"
	elif count > 500 and count < 1000:
		return "Novice"
	elif count > 1000 and count < 5000:
		return "Professional"
	elif count > 5000 and count < 10000:
		return "Addicted"
	elif count > 10000 and count < 20000:
		return "Hentai Lord"
	elif count > 20000 and count < 50000:
		return "Hentai God"
	elif count > 50000 and count < 100000:
		return "Hentai Demon"
	elif count > 100000 and count < 200000:
		return "ポルノ悪魔"
	elif count > 200000:
		return "オナニーの達人"


def rich_presence_loop():
	try:
		RPC = Presence("668374155434917900")
		RPC.connect()
		startup_time = int(time.time())
		count = system.database.query_file_count()
		RPC.update(details="Chilling on Onani Menu™", state=f"{count} images, Rank: {presence_rank(count)}",
				large_image="onani_original_logo", large_text=f"オナニー v{system.__version__}", start=startup_time)
	except:
		pass
	else:
		while True:
			time.sleep(15)
			if system.values.scraping:
				RPC.update(details="Scraping", state="What scrape doe???", large_image="onani_original_logo", large_text=f"オナニー v{system.__version__}", start=startup_time)
			elif system.values.downloading > 0:
				RPC.update(details="Finishing Downloads", state="Could be stuck who knows", large_image="onani_original_logo", large_text=f"オナニー v{system.__version__}", start=startup_time)
			elif system.values.hell:
				hell_time = 666
				RPC.update(details="  ", state="ΧΞϚ", large_image="onani_original_logo", large_text=f"オナニー v{system.__version__}", start=hell_time)
			else:
				try:
					count = system.database.query_file_count()
				except:
					pass
				else:
					RPC.update(details="Chilling on Onani Menu™", state=f"{count} images, Rank: {presence_rank(count)}", large_image="onani_original_logo", large_text=f"オナニー v{system.__version__}", start=startup_time)


def reset_values():
	system.values.found = list()
	system.values.downloaded = list()
	system.values.written = list()
	system.values.downloading = 0
	system.values.finished = 0
	system.values.shutdown_count = 0


def _all(list1, list2):
	list3 = list()
	for i in list1:
		if i in list2:
			list3.append(i)
		else:
			continue
	return list3 == list1


def _any(list1, list2):
	for i in list1:
		if i in list2:
			return True
		else:
			continue
	return False


def parse_tags(tag_string):
	reg = r"""(filename|artist|source|md5|filetype)?(:|-)([\d\w$-/:-?{-~!"^_`\[\]]{1,})"""
	tags = tag_string
	formt = {
		"all": False,
		"favourite": False,
		"filename": [],
		"artist": [],
		"source": [],
		"md5": [],
		"filetype": [],
		"whitelist": [],
		"blacklist": []
	}
	search_options = re.finditer(reg, tag_string)
	for match in search_options:
		if match.group(2) == "-":
			formt['blacklist'].append(match.group(3))
		else:
			formt[match.group(1)].append(match.group(3))
	formt['whitelist'].extend(re.sub(reg, "", tags).strip().split(" "))
	if "all" in formt['whitelist']:
		formt['all'] = True
	if "Favourites" in formt['whitelist']:
		formt['favourite'] = True
	return formt


def file_search_match(row, tags, current_user):
	add = False
	if not row[1] in tags['blacklist']:
		filetags = json.loads(row[3])
		if _all(tags['whitelist'], filetags):
			if not _any(tags['blacklist'], filetags):
				add = True
		
		if not _any(tags['blacklist'], filetags):
			if not add:
				meta = json.loads(row[4])
				if tags['favourite']:
					if {"location": row[1], "filename": row[0]} in current_user.favourites:
						if not _any(tags['blacklist'], filetags):
							add = True

				elif row[2] in tags['md5']:
					add = True

				elif len(tags['source']) > 0:
					for sauce in meta['sources']:
						if string in tags['source'][0]:
							add = True

				elif len(tags['artist']) > 0:
					if meta['artist'] == tags['artist'][0]:
						add = True

				elif len(tags['filename']) > 0:
					if tags['filename'][0] in row[0]:
						add = True

				elif row[1] in tags["whitelist"]:
					add = True
			if len(tags['filetype']) > 0:
				if os.path.splitext(row[0])[1].lstrip(".") in tags['filetype']:
					if _all(tags['whitelist'], filetags):
						add = True
					else:
						add = False
				else:
					add = False
	return add


def check_sauce(filepath):
	filename = filepath.split("/")[-1]
	directory = filepath.replace(filename, "")
	saucenao = SauceNao(directory=directory,
						databases=999, minimum_similarity=65)
	return saucenao.check_file(file_name=filename)


def write_to_file(filepath, content, mode="a"):
	with open(filepath, mode) as f:
		f.write(content)


def log_scrape(query, type, total=0, mode="start"):
	now = datetime.now().strftime("%H:%M:%S | %d/%m/%Y")
	if query == "":
		query = "None"
	if mode == "start":
		stri = f"[{now}]: Started Scraping: {query}, Type: {type}"
	elif mode == "stop":
		stri = f"[{now}]: Stopped Scraping: {query}, Total: {total}"
	with open(f"{system.dirs.user_log_dir}/scrape_log.txt", "a") as f:
		f.write(f"{stri}\n")

# https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside
def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
	text = text.split('/')[-1]
	return [atoi(c) for c in re.split(r'(\d+)', text)]


def plural_logic(number):
	if not int(number) == 1:
		return "s"
	else:
		return ""


def modify_filename(filename, buffer, location="Other"):
	md5 = get_md5(buffer, bytesio=True)
	return f"{filename}-{location}-{md5}"


def list_remove_empty(l):
	new_list = list()
	for item in l:
		if len(item) == 0:
			pass
		else:
			new_list.append(item)
	return new_list


def scan_dir_tree(directory):
	files = set()
	for root, dirs, files_ in os.walk(directory, topdown=False):
		for media in files_:
			if media.split(".")[-1] in system.allowed_filetypes:
				files.add(os.path.join(root, media).replace("\\", "/"))
	return list(files)


def add_local_files(files):
	for file in files:
		system.database.write_to_db(file['path'], "LocalFile", file["source"], file["tags"], artist=file["artist"])


def postive_num(number):
	return (number if number > -1 else 0)


# Not Important, Easter eggs #

def junk_text(len=50, chars=list(string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation)):
	junk = str()
	for x in range(len):
		junk += random.choice(chars)
	return junk


def random_word_string(len=200):
	actual_string = str()
	stri = str()
	for _ in range(len):
		for _ in range(random.randint(5, 10)):
			s = random_words(len=random.randint(1, 20))
			s.extend(list(str(junk_text(len=random.randint(100, 200)))))
			random.shuffle(s)
			stri += random.choice(string.ascii_uppercase + string.ascii_lowercase + string.punctuation + string.whitespace).join(s)
	for char in list(stri):
		if random.randint(1,10) == 1:
			char = random.choice(string.ascii_uppercase + string.ascii_lowercase + string.punctuation + string.whitespace)
		actual_string += char
	return actual_string


def corrupt_print(text, end="\n", flush=False):
	new_text = str()
	for char in text:
		if not char in string.whitespace:
			if random.randint(1,random.randint(1, 10)) == 1:
				char = str(chr(random.randint(8, 1000)))
		new_text += char
	print(new_text, end=end, flush=flush)


def bad():
	if not os.path.isfile(f"{system.dirs.user_data_dir}/ihavesinned.onani"):
		with open(f"{system.dirs.user_data_dir}/ihavesinned.onani", "wb") as f:
			f.write(os.urandom(681984))


def aaa():
	try:
		playsound("system/audio/aaa.mp3")
	except:
		pass


def fear():
	try:
		playsound("system/audio/fear.mp3")
	except:
		pass


def hell_type():
	greek_alphabet = [
			u'\u0391', u'\u0392', u'\u0393', u'\u0394',
			u'\u0395', u'\u0396', u'\u0397', u'\u0398',
			u'\u0399', u'\u039A', u'\u039B', u'\u039C',
			u'\u039D', u'\u039E', u'\u039F', u'\u03A0',
			u'\u03A1', u'\u03A3', u'\u03A4', u'\u03A5', 
			u'\u03A6', u'\u03A7', u'\u03A8', u'\u03A9', 
			u'\u03B1', u'\u03B2', u'\u03B3', u'\u03B4', 
			u'\u03B5', u'\u03B6', u'\u03B7', u'\u03B8', 
			u'\u03B9', u'\u03BA', u'\u03BB', u'\u03BC', 
			u'\u03BD', u'\u03BE', u'\u03BF', u'\u03C0', 
			u'\u03C1', u'\u03C3', u'\u03C4', u'\u03C5', 
			u'\u03C6', u'\u03C7', u'\u03C8', u'\u03C9']
	while system.values.hell:
		e = list()
		for x in range(5):
			e.append(random.choice(greek_alphabet))
		for char in list("".join(e) + chr(random.randint(8, 46))):
			if random.randint(1, 2) == 1:
				sys.stdout.write(char.lower())
			else:
				sys.stdout.write(char.upper())
			sys.stdout.flush()
			time.sleep(0.001)


def random_words(len=5):
	relines = list()
	with open("system/web/font/words.txt") as f:
		lines = f.read().splitlines()
	for _ in range(len):
		relines.append(random.choice(lines))
	return relines


def hells():
	if hell:
		return
	else:
		system.values.hell = True
	threading.Thread(target=hell_type, daemon=True).start()
	playsound("system/audio/hell.mp3")
	system.values.hell = False


# OLD 

# def db_writer_thread():
# 	while True:
# 		values = system.database_write_queue.get()
# 		if values is None:
# 			pass
# 		else:
# 			system.database.write_to_db(values[0], values[1], values[2], values[3])
# 			system.database_write_queue.task_done()

# def parse_webviewer_link(link):
# 	filepath = re.search(
# 		"database\/[a-zA-Z0-9]{1,10}/[a-zA-Z0-9_-]{1,}\.[a-zA-Z]{3,4}", link)
# 	if filepath is None:
# 		return None, None
# 	else:
# 		table = filepath.group(0).split("/")[1]
# 		return filepath.group(0), table

# def type(text, delay=0.5):
# 	for char in list(text):
# 		print(char, end="")
# 		time.sleep(delay)
# 	print("\n")

# def create_post_id():
# 	"""
# 	Create a post id
# 	"""
# 	id = list()
# 	for x in range(8):
# 		id.append(random.choice(string.ascii_letters + string.digits))
# 	return ''.join(id)
