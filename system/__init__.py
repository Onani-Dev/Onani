import base64
import datetime
import getpass
import json
import os
import queue
import random
import shutil
import socketserver
import sqlite3
import subprocess
import sys
import time
from base64 import b16decode as b58
from collections import deque

import psutil
from appdirs import AppDirs

# onani version info
__version_info__ = (2, 0, 0, "20.2b")
__version__ = '.'.join(map(str, __version_info__))
db_version = 2


# setup directories
dirs = AppDirs("Onani")
if not os.path.isdir(dirs.user_data_dir):
	os.makedirs(dirs.user_data_dir, exist_ok=True)
if not os.path.isdir(dirs.user_log_dir):
	os.makedirs(dirs.user_log_dir, exist_ok=True)


# initialize DB
print("Initializing Database")
if not os.path.isdir("database"):
	os.mkdir("database")
conn = sqlite3.connect('database/data.db')
c = conn.cursor()
if not os.path.isdir("database/sauce"):
	os.mkdir("database/sauce")
if not os.path.isdir("database/Other"):
	os.mkdir("database/Other")
if not os.path.isdir('database/OnaniUploaded'):
	os.mkdir("database/OnaniUploaded")
_current_ver = c.execute("PRAGMA user_version;").fetchone()[0]
if _current_ver < db_version:
	print(f"Upgrading database... (v{_current_ver} => v{db_version})")
	c.execute('CREATE TABLE IF NOT EXISTS OnaniFiles (filename TEXT PRIMARY KEY, location TEXT, "md5" TEXT, tags JSON, meta JSON);')
	c.execute('CREATE TABLE IF NOT EXISTS OnaniUsers (username TEXT PRIMARY KEY, password TEXT, is_admin INTEGER, api_key TEXT, favourites JSON, settings JSON);')
	c.execute('CREATE TABLE IF NOT EXISTS OnaniCollections (id INTEGER PRIMARY KEY, name TEXT, meta JSON, files JSON);')
	c.execute("CREATE INDEX IF NOT EXISTS FileIndex ON OnaniFiles(filename);")
	c.execute("CREATE INDEX IF NOT EXISTS UserIndex ON OnaniUsers(username);")
	c.execute("CREATE INDEX IF NOT EXISTS CollectionIndex ON OnaniCollections(id);")
	c.execute(f"PRAGMA user_version = {db_version};")
	_current_ver = db_version
elif db_version < _current_ver:
	print("[WARNING] Database version is higher than this version of onani was made to work with.")
	input("Press enter to continue.")
conn.commit()
conn.close()
print(f"Initialized Onani DB v{_current_ver}")


# backup database
if not os.path.isdir(f"{dirs.user_data_dir}/DatabaseBackup/"):
	os.mkdir(f"{dirs.user_data_dir}/DatabaseBackup/")
shutil.copy("database/data.db", f"{dirs.user_data_dir}/DatabaseBackup/data.db.{datetime.datetime.now().strftime('%d-%m-%Y_%I-%M%p')}.bak")


def setup_settings(validjson=False):
	default = {
		"scraper_threadcount": 50,
		"enable_discord_presence": False,
		"new_print_style": True,
		"eHentai_username": None,
		"eHentai_password": None,
		"web_viewer_port": 5000,
		"webviewer_secret_key": base64.b85encode(os.urandom(12)).decode(),
		"api_debug": False
	}
	if validjson:
		default.update(json.loads(open(f'{dirs.user_data_dir}/config.json').read()))
	original = dict(default)
	# first time setup
	if validjson:
		print(f"Welcome back to Onani, {getpass.getuser()}!\nThe config was missing a value, so please review your config.")
	else:
		print(f"Welcome to Onani, {getpass.getuser()}!\nPlease enter info for first time use.")
	try:
		default["scraper_threadcount"] = int(input(f'Scraper Thread Count ({original["scraper_threadcount"]}): '))
	except:
		default["scraper_threadcount"] = original["scraper_threadcount"]
	default["enable_discord_presence"] = input(f"Enable Discord Rich Presence? <y/n> ({original['enable_discord_presence']}): ")
	if default["enable_discord_presence"].lower() == "y":
		default["enable_discord_presence"] = True
	elif default["enable_discord_presence"].lower() == "n":
		default["enable_discord_presence"] = False
	else:
		default["enable_discord_presence"] = original['enable_discord_presence']
	try:
		default["web_viewer_port"] = int(input(f"Web Viewer Port ({original['web_viewer_port']}): "))
	except:
		print('Defaulting to', original['web_viewer_port'])
		default["web_viewer_port"] = original['web_viewer_port']
	else:
		if default["web_viewer_port"] > 65535:
			default["web_viewer_port"] = 65535
		elif default["web_viewer_port"] < 1:
			default["web_viewer_port"] = 1
	with open(f'{dirs.user_data_dir}/config.json', mode="w") as f:
		json.dump(default, f, indent=4)

# load config
if os.path.isfile('system/config.json'):
	shutil.move("system/config.json", f"{dirs.user_data_dir}/config.json")
if not os.path.isfile(f"{dirs.user_data_dir}/config.json"):
	setup_settings()
while True:
	try:
		try:
			config = json.loads(open(f"{dirs.user_data_dir}/config.json").read())
		except:
			validjson = False
		else:
			validjson = True
		scraper_threadcount = config["scraper_threadcount"]
		enable_discord_presence = config["enable_discord_presence"]
		web_viewer_port = config["web_viewer_port"]
		new_print_style = config["new_print_style"]
		ehentai_username = config["eHentai_username"]
		ehentai_password = config["eHentai_password"]
		webviewer_secret_key = base64.b85decode(config["webviewer_secret_key"])
		api_debug = config["api_debug"]
	except:
		if validjson:
			print("Config is out of date.")
		else:
			print("Config is corrupted or missing.")
		setup_settings(validjson=validjson)
	else:
		break

# game
eval(compile(b58("""69662072616E646F6D2E72616E64696E7428312C2035303029203D3D20313A0A09666F72206368617220696E206C697374282248454C4C4F5C6E5C6E22293A0A09097072696E7428636861722C20656E643D22222C20666C7573683D54727565290A090974696D652E736C65657028302E31290A09666F72206368617220696E206C69737428225348414C4C20574520504C415920412047414D453F22293A0A09097072696E7428636861722C20656E643D22222C20666C7573683D54727565290A090974696D652E736C65657028302E31290A0974696D652E736C6565702835290A6E6F6E6F6C697374203D205B22646F6E222C2022646F6E5F6368616E222C2022646F6E206368616E222C2022646F6E2D6368616E222C20227461696B6F222C20227461696B6F5F6E6F5F74617473756A696E222C20226B61747375222C20226B617473755F6368616E222C20226B61747375206368616E222C20226B617473752D6368616E222C20226B61745F6368616E222C20226B6174206368616E222C20226B61742D6368616E222C2022E5A4AAE9BC93E381AEE98194E4BABA225D0A6966206F732E706174682E697366696C652866227B646972732E757365725F646174615F6469727D2F696861766573696E6E65642E6F6E616E6922293A0A096861735F73696E6E6564203D20547275650A096966206E6F742022666C61736B2220696E207379732E6D6F64756C65733A0A09097072696E74286F732E7572616E646F6D2836363636292E6465636F646528227574662D38222C206572726F72733D227265706C6163652229290A656C73653A0A096861735F73696E6E6564203D2046616C73650A666F72206520696E205B22417661737455492E657865222C2022617377456E675372762E657865225D3A0A096966206520696E206C6973742828702E6E616D65282920666F72207020696E2070737574696C2E70726F636573735F69746572282929293A0A0909666F72206368617220696E206C6973742822507373742E5C6E22293A0A0909097072696E7428636861722C20656E643D22222C20666C7573683D54727565290A09090974696D652E736C65657028302E3035290A090974696D652E736C6565702833290A0909666F72206368617220696E206C69737428224176617374206973207265616C6C79206372696E67652E20596F75206B6E6F7720746861742072696768743F5C6E22293A0A0909097072696E7428636861722C20656E643D22222C20666C7573683D54727565290A09090974696D652E736C65657028302E3035290A090974696D652E736C6565702833290A0909666F72206368617220696E206C697374282244656C6574652069742E5C6E22293A0A0909097072696E7428636861722C20656E643D22222C20666C7573683D54727565290A09090974696D652E736C65657028302E3035290A090974696D652E736C6565702833290A0909627265616B"""), '<string>', 'exec'), globals(), locals())
splashes = ['Hows this for splash text?', 'Welcome to the cum zone.',
            'Onani > RTB', 'Desu Wa', 'Put images in here you cuck', 'ft. Hatsune Miku',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'anal sex', 'SEX',
            'Objects that i\'ve shoved up my ass', 'don\'t scrape don', 'Masturbation',
            'look at this virgin about to look at hentai', 'cum', 'Only cum inside anime girls.',
            'Onani | オナニー Copyright © 2020 blakeando', 'オナニー', f'Onani v{__version__}',
            'Cum Machine', 'DeadBread is Dead.', f'disgust{random.randint(1,11)}.png',
            'poo', 'piss your pants', 'Cock and ball Torture',
            'Hentai is art.', '😳', ':flushed:',
            'mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm', 'drink cum for fun', 'My dick is in love with pain',
            os.urandom(9).decode("utf-8", errors="replace"), 'Click the circles', '666',
            'Have you sinned?', 'allo', '83% Python',
            '@everyone', 'オナニーの達人', 'sex with the homies 😩',
            '1man', 'emailGecko.py', 'I actually beat a nerd to death.',
            'Not Trans.', '13 and Depressed? That means ur a girl take these pills put on these socks and post nudes in my discord server',
            'shit and piss and cum', 'Giantess Vore MMMMMMM', 'bruh',
            'hot sauce anal sandwich', os.urandom(35).decode("utf-8", errors="replace"), 'Full of futa cum.',
			'angogogogoanan', 'Not Django', ' DJ Ango',
			'Cool!', 'Compatible with nothing', 'Buggy']


# start uptime counter
uptime = time.time()


# create queues
print_queue = deque()
logger_queue = queue.Queue()
database_write_queue = queue.Queue()
viewer_scraper_queue = deque()


# list of allowed filetypes
allowed_filetypes = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'jfif', 'webm', 'mp4']


# All folders
folders = ['DanBooru', 'GelBooru', 'GiantessBooru', 'HentaiCosplay',
           'HentaiFoundry', 'HypnoHub', 'KonaChan',
           'Other', 'RealBooru', 'Rule34', 'Rule34Hentai',
           'Rule34Paheal', 'Twitter', 'Waifu2x', 'XBooru',
           'Yandere', 'eHentai', 'SankakuComplex', 'YiffParty', 'e621', 'OnaniUploaded']


# default user settings
default_user_settings = {
	"free_hand": "left",
	"sfw_mode": False,
	"splash_text": False
}


# check ffmpeg
try:
	subprocess.check_output(['ffmpeg', '-h'], stderr=subprocess.DEVNULL)
except:
	print("[WARNING] FFMpeg not present. Thumbnails for videos will not be made.")
	input("Press enter to continue.")
else:
	if not has_sinned:
		print("FFMpeg OK")

# from concurrent.futures import ThreadPoolExecutor
# # monkey patching - "look at this fucking mess"
# socketserver.monkeypool = ThreadPoolExecutor(max_workers=webviewer_threadcount)

# def process_request(self, request, client_address):
# 	socketserver.monkeypool.submit(self.process_request_thread, request, client_address)

# socketserver.ThreadingMixIn.process_request = process_request
