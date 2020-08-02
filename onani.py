#  ▄██████▄  ███▄▄▄▄      ▄████████ ███▄▄▄▄    ▄█          ▄████████    ▄████████  ▄█     █▄     ▄████████  ▄█      ███         ███        ▄████████ ███▄▄▄▄   
# ███    ███ ███▀▀▀██▄   ███    ███ ███▀▀▀██▄ ███         ███    ███   ███    ███ ███     ███   ███    ███ ███  ▀█████████▄ ▀█████████▄   ███    ███ ███▀▀▀██▄ 
# ███    ███ ███   ███   ███    ███ ███   ███ ███▌        ███    ███   ███    █▀  ███     ███   ███    ███ ███▌    ▀███▀▀██    ▀███▀▀██   ███    █▀  ███   ███ 
# ███    ███ ███   ███   ███    ███ ███   ███ ███▌       ▄███▄▄▄▄██▀  ▄███▄▄▄     ███     ███  ▄███▄▄▄▄██▀ ███▌     ███   ▀     ███   ▀  ▄███▄▄▄     ███   ███ 
# ███    ███ ███   ███ ▀███████████ ███   ███ ███▌      ▀▀███▀▀▀▀▀   ▀▀███▀▀▀     ███     ███ ▀▀███▀▀▀▀▀   ███▌     ███         ███     ▀▀███▀▀▀     ███   ███ 
# ███    ███ ███   ███   ███    ███ ███   ███ ███       ▀███████████   ███    █▄  ███     ███ ▀███████████ ███      ███         ███       ███    █▄  ███   ███ 
# ███    ███ ███   ███   ███    ███ ███   ███ ███         ███    ███   ███    ███ ███ ▄█▄ ███   ███    ███ ███      ███         ███       ███    ███ ███   ███ 
#  ▀██████▀   ▀█   █▀    ███    █▀   ▀█   █▀  █▀          ███    ███   ██████████  ▀███▀███▀    ███    ███ █▀      ▄████▀      ▄████▀     ██████████  ▀█   █▀  
#                                                         ███    ███                            ███    ███                                                     
# Onani by blakeando
# Originally created: 24/09/2019 4:19 AM 
# Rewritten: 2/01/2020 11:24 PM - 19/01/2020 12:30 PM
# Put argument 'boorumation_start' to start BooruMation as soon as Onani boots.


import os
import random
import re
import shutil
import sys
import threading
import time
import webbrowser

from colorama import init
from pyfiglet import Figlet
from termcolor import colored

import system.database
import system.download
import system.title
import system.values
from scrapers import e_hentai
from system.controller import *
from system.engine import *
from system.web_server import start_web_viewer


# .d8888.  .o88b. d8888b.  .d8b.  d8888b. d88888b d8888b.      d888888b d8b   db d888888b d888888b d888888b  .d8b.  d888888b  .d88b.  d8888b. .d8888. 
# 88'  YP d8P  Y8 88  `8D d8' `8b 88  `8D 88'     88  `8D        `88'   888o  88   `88'   `~~88~~'   `88'   d8' `8b `~~88~~' .8P  Y8. 88  `8D 88'  YP 
# `8bo.   8P      88oobY' 88ooo88 88oodD' 88ooooo 88oobY'         88    88V8o 88    88       88       88    88ooo88    88    88    88 88oobY' `8bo.   
#   `Y8b. 8b      88`8b   88~~~88 88~~~   88~~~~~ 88`8b           88    88 V8o88    88       88       88    88~~~88    88    88    88 88`8b     `Y8b. 
# db   8D Y8b  d8 88 `88. 88   88 88      88.     88 `88.        .88.   88  V888   .88.      88      .88.   88   88    88    `8b  d8' 88 `88. db   8D 
# `8888Y'  `Y88P' 88   YD YP   YP 88      Y88888P 88   YD      Y888888P VP   V8P Y888888P    YP    Y888888P YP   YP    YP     `Y88P'  88   YD `8888Y' 


def start_scrape(query, max_downloads):
	log_scrape(query, "Normal Scrape")
	system.values.scraping = True
	scrape_controller(query, max_downloads)
	stop_scraping()
	log_scrape(query, "Normal Scrape", total=len(
		system.values.downloaded), mode="stop")


def start_custom_scrape(query, max_downloads):
	log_scrape(query, "Custom Scrape")
	system.values.scraping = True
	custom_scrape_controller(query, max_downloads)
	stop_scraping()
	log_scrape(query, "Custom Scrape", total=len(
		system.values.downloaded), mode="stop")


def start_ehentai_scrape(query):
	log_scrape(query, "e-Hentai Gallery Download")
	system.values.scraping = True
	ehentai_scrape_controller(query)
	stop_scraping(passive=True)
	log_scrape(query, "e-Hentai Gallery Download", total=len(
		system.values.downloaded), mode="stop")


def start_twitter_scrape(query):
	log_scrape(query, "Twitter Image Scrape")
	system.values.scraping = True
	twitter_scrape_controller(query)
	stop_scraping(passive=True)
	log_scrape(query, "Twitter Image Scrape", total=len(
		system.values.downloaded), mode="stop")


def start_yiff_scrape(query, threads):
	log_scrape(query, "yiff.party Gallery Download")
	system.values.scraping = True
	yiff_scrape_controller(query, threads)
	stop_scraping(passive=True)
	log_scrape(query, "yiff.party Gallery Download", total=len(
		system.values.downloaded), mode="stop")


def start_boorumation():
	log_scrape("All Latest Posts", "Boorumation")
	system.values.scraping = True
	boorumation_controller()
	stop_scraping()
	log_scrape("All Latest Posts", "Boorumation", total=len(
		system.values.downloaded), mode="stop")


# .88b  d88. d88888b d8b   db db    db      d888888b d888888b d88888b .88b  d88. .d8888. 
# 88'YbdP`88 88'     888o  88 88    88        `88'   `~~88~~' 88'     88'YbdP`88 88'  YP 
# 88  88  88 88ooooo 88V8o 88 88    88         88       88    88ooooo 88  88  88 `8bo.   
# 88  88  88 88~~~~~ 88 V8o88 88    88         88       88    88~~~~~ 88  88  88   `Y8b. 
# 88  88  88 88.     88  V888 88b  d88        .88.      88    88.     88  88  88 db   8D 
# YP  YP  YP Y88888P VP   V8P ~Y8888P'      Y888888P    YP    Y88888P YP  YP  YP `8888Y'


def _open_webviewer(q):
	webbrowser.open_new_tab(f"http://127.0.0.1:{system.web_viewer_port}/")


def _start_scrape_menu(q):
	clear()
	print(title)
	q = input(colored("\nTags/Query: ", "red"))
	if q == "0":
		pass
	else:
		max_downloads = input(
			colored(f"Maximum Concurrent Downloads (Default {system.scraper_threadcount}): ", "red"))
		if max_downloads.rstrip() == "":
			max_downloads = system.scraper_threadcount
		else:
			try:
				max_downloads = int(max_downloads)
			except:
				max_downloads = 50
		if q in system.nonolist:
			print("Perish.")
			system.engine.bad()
			time.sleep(3)
			threading.Thread(target=hells, daemon=True).start()
			while True:
				pass
		start_scrape(q, max_downloads)


def _start_custom_scrape_menu(q):
	def toggle_value(val):
		system.values.custom_dict[val] = opposite_bool(system.values.custom_dict[val])
	autotags = [
		'DanBooru', 'e621', 'GelBooru', 
		'Giantess Booru', 'HypnoHub', 
		'KonaChan', 'RealBooru', 'Rule 34', 
		'XBooru', 'Yande.re', 'Sankaku Complex'
		]
	switch = {
		"0": ""
	}
	count = 0
	for site in sorted(list(system.values.custom_dict)):
		count += 1
		switch[str(count)] = site
	while True:
		clear()
		reset_values()
		print(title)
		print(colored("\n\nType Number To Toggle. Press enter with no input to start. Options with (AutoTag) automatically tag themselves.\n", "red"))
		print(colored("0.  Go Back", "red"))
		for site in list(switch.keys()):
			if site == '0':
				pass
			else:
				string = str()
				string += f"{site}.  {switch[site]}: {system.values.custom_dict[switch[site]]}"
				if switch[site] in autotags: string += " (AutoTag)"
				print(colored(string, "red"))
		t = input(colored("> ", "red"))
		if t == "0":
			break
		elif t == "all":
			for key in list(system.values.custom_dict):
				toggle_value(key)
		elif t == "autotag":
			for site in autotags:
				toggle_value(site)
		elif t == "":
			clear()
			print(title)
			q = input(colored("\nTags/Query: ", "red"))
			if q == "0":
				pass
			else:
				max_downloads = input(
					colored(f"Maximum Concurrent Downloads (Default {system.scraper_threadcount}): ", "red"))
				if max_downloads.rstrip() == "":
					max_downloads = system.scraper_threadcount
				else:
					try:
						max_downloads = int(max_downloads)
					except:
						max_downloads = system.scraper_threadcount
				if q in system.nonolist:
					print("Perish.")
					system.engine.bad()
					time.sleep(3)
					threading.Thread(target=hells, daemon=True).start()
					while True:
						pass
				start_custom_scrape(q, max_downloads)
		else:
			try:
				togg = switch.get(t, lambda e: None)
				system.values.custom_dict[togg] = opposite_bool(system.values.custom_dict[togg])
			except:
				pass


def _add_images(q):
	clear()
	if gui:
		filepaths = askopenfilenames(initialdir=os.getcwd(), title="Select Image to add to DB",
										filetypes=(("Image and Video files", "*.jpg *.jpeg *.png *.gif *.mp4 *.webm"), ("All files", "*.*")))
		if len(filepaths) == 0:
			pass
		else:
			print(title)
			tags = input(colored("\nTags for this image(s) (Split with comma): ", 'red')).replace(" ", "_").rstrip().split(",")
			print(colored("Adding...", 'red'))
			for filepath in filepaths:
				if not os.path.isfile(filepath):
					pass
				else:
					file = filepath.split('/')[-1]
					file_extension = file.split(".")[-1]
					file = make_safe_filename(file.split(".")[0])
					safe_file = uniquify(f"database/Other/{file}.{file_extension}")
					try:
						if not os.path.isdir("database/Other/"):
							os.mkdir("database/Other/")
						shutil.copy(filepath, safe_file)
					except Exception as e:
						log_exception(e)
					else:
						system.database.write_to_db("Other", safe_file, filepath, tags)
	else:
		print("Sorry, no GUI is found.")
		input()


def _verify_db_menu(q):
	clear()
	print(title)
	print(colored("Are you sure? <y/n>:"))
	e = input("")
	if e.lower() == "y":
		start = time.time()
		system.database.verify_db()
		end = time.time()
		input(f"Task Completed in {round(end - start, 2)} seconds.\nPress enter to continue.")


def _downloader_menu(q):
	while True:
		reset_values()
		clear()
		print(title)
		print(colored("\nDownloader Menu", "red"))
		print(colored("""
	0)  Back
	1)  e-Hentai
	2)  Twitter
	3)  Yiff.party""", "red"))
		if system.ehentai_username is not None and system.ehentai_password is not None:
			print(colored("""	4)  Check e-Hentai limits""", "red"))
		try:
			q = input(colored("> ", "red"))
		except KeyboardInterrupt:
			print("\nBye Bye!")
			sys.exit()

		if q == "0":
			break

		elif q == "1":
			clear()
			print(title)
			q = input(colored("\nLink: ", "red"))
			if re.match("https:\/\/e-hentai\.org\/g\/[0-9]{1,9}\/[a-zA-Z0-9]{1,10}/", q) is None:
				input("Not an e-hentai.org link.")
			else:
				start_ehentai_scrape(q)

		elif q == "2":
			clear()
			print(title)
			q = input(colored("\nUser: @", "red"))
			if q == "0":
				continue
			else:
				start_twitter_scrape(q)

		elif q == "3":
			clear()
			print(title)
			q = input(colored("\nLink: ", "red"))
			if re.match("https:\/\/yiff\.party\/[\w\d]{1,}\/[\d]{1,}", q) is None:
				input("Not a yiff.party link.")
			else:
				threads = input(colored("Thread Count (Default 10): ", "red"))
				if threads.isdigit():
					threads = int(threads)
				else:
					threads = 10
				start_yiff_scrape(q, threads)

		elif q == "4":
			if system.ehentai_username is not None and system.ehentai_password is not None:
				clear()
				print(title)
				e_hentai.check_limits()
				input()


def _boorumation(q):
	clear()
	print(title)
	print("\nPress Enter to stop looking for new posts.")
	start_boorumation()


def _sendtohell(q):
	threading.Thread(target=hells, daemon=True).start()


def _console(q):
	clear()
	print(title)
	print(colored("\nOnani Console\nType 'exit' to exit console.", 'red'))
	while True:
		com = input("> ")
		if com == "exit":
			break
		try:
			print(eval(com, globals(), locals()))
		except Exception as e:
			print(e)


def _scandir(q):
	clear()
	print(title)
	while True:
		directory, tags_string, artist, source, confirm = (
			input(colored("\nDirectory: ", "red")), 
			input(colored("Tags (Leave blank for 'None'):", "red")),
			input(colored("Artist (Leave blank for 'Unknown'):", "red")),
			input(colored("Source (Leave blank for 'Unknown'):", "red")),
			input(colored("Is this correct? <y/n>:", "red"))
			)
		if directory == "0" or confirm == "0":
			break
		if confirm.lower() == "y":
			break
	if directory == "0":
		pass
	else:
		files = scan_dir_tree(directory.strip().replace("\\", "/"))
		filedicts = list()
		for file in files:
			tags = (tags_string.split(" ") if len(tags_string) > 0 else ['None'])
			tags.append(file.split("/")[-2])
			filedicts.append({
				"path": file,
				"tags": tags,
				"source": (source.strip() if len(source.strip()) > 0 else 'Unknown'),
				"artist": (artist.strip() if len(artist.strip()) > 0 else 'Unknown')
			})
		print("Starting Background thread...")
		threading.Thread(target=add_local_files, args=(filedicts,), daemon=True).start()
		print(f"Done. Added {len(files)} files to database.")
		input()


def _manage_users(q):
	while True:
		clear()
		print(title)
		print(colored("""
		0) Back
		1) Add User
		2) Remove User
		3) Promote/Demote User
		""", "red"))
		try:
			q = input(colored("> ", "red"))
		except KeyboardInterrupt:
			print("\nBye Bye!")
			sys.exit()

		if q == "0":
			break

		elif q == "1":
			clear()
			print(title)
			username, password, confirmpass, admin = (input(colored("Username: ", "red")), system.getpass.getpass(colored("Password: ", "red")), system.getpass.getpass(colored("Confirm: ", "red")), input(colored("Admin <y/n>: ", "red")))
			if password == confirmpass:
				admin = (True if admin.lower() == "y" else False)
				result = system.database.create_user(username, password, admin=admin)
				input(f"{result['username']}{('(Admin)' if result['is_admin'] else '')}: Account created.")
			else:
				input("Password does not match.")
		
		elif q == "2":
			clear()
			print(title)
			username, confirm = (input(colored("Username: ", "red")), input(colored("Again to confirm: ", "red")))
			if username == confirm:
				system.database.delete_user(username)
		
		elif q == "3":
			clear()
			print(title)
			username = input(colored("Username: ", "red"))
			user = system.database.get_user(username)
			if user is not None:
				print(colored(f"User will be {('Demoted' if user['is_admin'] else 'Promoted')}. Ok? <y/n>:", "red"))
				confirm = input()
				if confirm.lower() == "y":
					system.database.promote_user(username, user['is_admin'])


# d8888b. db    db d8b   db      d888888b d8b   db d888888b d88888b d8888b. d88888b  .d8b.   .o88b. d88888b       .d8b.  d8b   db d8888b.      db   d8b   db d88888b d8888b. db    db d888888b d88888b db   d8b   db d88888b d8888b. 
# 88  `8D 88    88 888o  88        `88'   888o  88 `~~88~~' 88'     88  `8D 88'     d8' `8b d8P  Y8 88'          d8' `8b 888o  88 88  `8D      88   I8I   88 88'     88  `8D 88    88   `88'   88'     88   I8I   88 88'     88  `8D 
# 88oobY' 88    88 88V8o 88         88    88V8o 88    88    88ooooo 88oobY' 88ooo   88ooo88 8P      88ooooo      88ooo88 88V8o 88 88   88      88   I8I   88 88ooooo 88oooY' Y8    8P    88    88ooooo 88   I8I   88 88ooooo 88oobY' 
# 88`8b   88    88 88 V8o88         88    88 V8o88    88    88~~~~~ 88`8b   88~~~   88~~~88 8b      88~~~~~      88~~~88 88 V8o88 88   88      Y8   I8I   88 88~~~~~ 88~~~b. `8b  d8'    88    88~~~~~ Y8   I8I   88 88~~~~~ 88`8b   
# 88 `88. 88b  d88 88  V888        .88.   88  V888    88    88.     88 `88. 88      88   88 Y8b  d8 88.          88   88 88  V888 88  .8D      `8b d8'8b d8' 88.     88   8D  `8bd8'    .88.   88.     `8b d8'8b d8' 88.     88 `88. 
# 88   YD ~Y8888P' VP   V8P      Y888888P VP   V8P    YP    Y88888P 88   YD YP      YP   YP  `Y88P' Y88888P      YP   YP VP   V8P Y8888D'       `8b8' `8d8'  Y88888P Y8888P'    YP    Y888888P Y88888P  `8b8' `8d8'  Y88888P 88   YD 


if __name__ == "__main__":
	init()
	web = threading.Thread(target=start_web_viewer, name='Onani_WebViewerThread', daemon=True)
	web.start()
	try:
		from tkinter import *
		from tkinter.filedialog import *
		Tk().withdraw()
	except:
		gui = False
	else:
		gui = True
	threading.Thread(target=system.engine.print_thread, daemon=True, name='Onani_PrintThread').start()
	threading.Thread(target=system.engine.logger_thread, daemon=True, name='Onani_LoggerThread').start()
	threading.Thread(target=startup, daemon=True, name='Onani_StartupNoise').start()
	threading.Thread(target=system.title.startup_title, daemon=True, name='Onani_StartupTitle').start()
	if system.enable_discord_presence:
		threading.Thread(target=rich_presence_loop, daemon=True, name='Onani_DiscordRPC').start()
	if len(sys.argv) > 1:
		if sys.argv[1] == "boorumation_start":
			clear()
			print(colored("\t\tONANI", "red"))
			print("\nPress Enter to stop looking for new posts.")
			start_boorumation()

	if random.randint(1, 50) == 1:
		title = "\n\n"
		for line in colored(Figlet(font='system/fonts/Bloody').renderText('O FUCK'), "red").splitlines():
			title += f"\t\t{line}\n"

	elif random.randint(1, 20) == 1:
		title = colored(open('system/fonts/title2').read(), "red")

	elif random.randint(1, 50) == 1:
		title = "\n\n"
		for line in colored(Figlet(font='system/fonts/Bloody').renderText('ONAMI'), "red").splitlines():
			title += f"\t\t{line}\n"
	else:
		title = "\n\n"
		for line in colored(Figlet(font='system/fonts/Bloody').renderText('ONANI'), "red").splitlines():
			title += f"\t\t{line}\n"

	if system.has_sinned:  # YandereDev would be proud
		def print(text, end="\n", flush=False):
			system.engine.corrupt_print(text, end=end, flush=flush)

	while True:
		reset_values()
		clear()
		print(title)
		print(colored("""
		0)  Open WebViewer
		1)  Scrape
		2)  Custom Scrape
		3)  Add Image(s) to Database
		4)  Verify Database
		5)  Downloader Menu
		6)  DanBooru Boorumation
		7)  User Management
		8)  Scan external directories
		""", "red"))

		try:
			q = input(colored("> ", "red"))
		except KeyboardInterrupt:
			print("\nBye Bye!")
			sys.exit()

		if system.has_sinned:
			clear()
			m = "\n\n"
			for line in colored(Figlet(font='system/fonts/Bloody').renderText('DIE'), "red").splitlines():
				m += f"\t\t{line}\n"
			print(m)
			if q == "0":
				webbrowser.open_new_tab(f"http://127.0.0.1:{system.web_viewer_port}/fun")
			else:
				threading.Thread(target=fear, daemon=True, name='Onani_Fear').start()
			time.sleep(10)
			continue

		count = 0
		for a in q.upper():
			if not a == "A":
				count = 0
				break
			else:
				count += 1

		if count > 10:
			threading.Thread(target=aaa, daemon=True, name='Onani_Scream').start()

		func = {
			"0": _open_webviewer,
			"1": _start_scrape_menu,
			"2": _start_custom_scrape_menu,
			"3": _add_images,
			"4": _verify_db_menu,
			"5": _downloader_menu,
			"6": _boorumation,
			"7": _manage_users,
			"8": _scandir,
			"666": _sendtohell,
			"console": _console,
			"exit": lambda q: sys.exit()
		}.get(q, lambda e: None)
		if not system.values.scraping:
			func(q)
		else:
			while system.values.shutdown_count > 0 or system.values.downloading > 0:
				time.sleep(.01)
			func(q)
