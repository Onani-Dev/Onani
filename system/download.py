import os
import platform
import re
import sys
import time
import urllib.parse
import zipfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO, StringIO

import humanize
import PIL.Image
import requests
from termcolor import colored

import system.database
import system.engine
import system.title
import system.values
import system.exceptions

try:
	headers = {
		"User-Agent": f"Onani/{system.__version__} ({platform.system()} {platform.release()} {platform.version()}; {sys.platform}) Python/{platform.python_version()} Requests/{requests.__version__}"}
except:
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}


def parse_filename(filename):
	original_name = filename.split("/")[-1]
	file_type = original_name.split(".")[-1]
	if "?" in file_type:
		file_type = file_type.split("?")[0]
	filename = system.engine.make_safe_filename(urllib.parse.unquote(
		original_name.replace(f".{file_type}", "")))
	return original_name, file_type, filename


def match_download_location(file):
	regex_list = {
		"DanBooru": ["https:\/\/danbooru\.donmai\.us\/data\/[a-zA-Z0-9._-]{1,}",
					"https:\/\/[a-zA-Z0-9._-]{1,}\.donmai\.us\/original\/[a-zA-Z0-9._-]{1,}/[a-zA-Z0-9._-]{1,}\/[a-zA-Z0-9._-]{1,}\.[a-zA-Z0-9._-]{1,}"],
		"GelBooru": ["https:\/\/img.\.gelbooru\.com\/images\/[\w\d]{2}\/[\w\d]{2}\/[\w\d]{32}\.[\w\d]{2,4}"],
		"GiantessBooru": ["https:\/\/giantessbooru\.com\/_images\/[a-zA-Z0-9]{1,}\/[a-zA-Z0-9._-]{1,}"],
		"HypnoHub": ["https:\/\/hypnohub\.net\/\/data\/[a-z]{1,}\/[a-zA-Z0-9._-]{1,}"],
		"KonaChan": ["https:\/\/konachan\.com\/[a-z]{1,}\/[a-zA-Z0-9]{1,}\/[a-zA-Z0-9%._-]{7,}"],
		"RealBooru": ["https:\/\/realbooru\.com\/images\/[0-9]{1,}\/[a-zA-Z0-9._-]{1,}"],
		"Rule34Paheal": ["https:\/\/[a-zA-Z0-9]{1,}\.paheal\.net\/_images\/[a-zA-Z0-9]{1,}\/[a-zA-Z0-9._%-]{1,}"],
		"Rule34": ["https:\/\/..\.rule34\.xxx\/images\/[0-9]{1,}\/[a-zA-Z0-9._-]{1,}", 
					"https:\/\/img\.rule34\.xxx\/images\/[0-9]{1,10}/[a-zA-Z0-9]{1,}\.[a-zA-Z]{3,4}",
                    "https:\/\/..webm\.rule34\.xxx\/images\/[0-9]{1,}\/[a-zA-Z0-9._-]{1,}",
                    "https:\/\/rule34\.xxx\/images\/[0-9]{1,}\/[a-zA-Z0-9._-]{1,}"],
		"XBooru": ["https:\/\/img\.xbooru\.com\/[a-zA-Z0-9]{1,}\/[0-9]{1,}\/[a-zA-Z0-9._-]{1,}"],
		"Yandere": ["https:\/\/files\.yande\.re\/[a-z]{1,}\/[a-zA-Z0-9]{1,}\/[a-zA-Z0-9%._-]{1,}"],
		"Twitter": ["http:\/\/pbs\.twimg\.com\/media\/[a-zA-Z0-9_-]{1,}\.png", 
					"https:\/\/video\.twimg\.com\/ext_tw_video\/[\d]{19}\/pu\/vid\/[\dx]{1,}/[\d\w\W\D]{1,}\.mp4"],
		"eHentai": ["[0-9a-zA-Z_;:.-\/]{1,}\/h\/[a-zA-Z0-9%._-]{1,}\/keystamp=[a-zA-Z0-9%._-]{1,};fileindex=[a-zA-Z0-9]{1,};xres=[a-zA-Z0-9]{1,}/[a-zA-Z0-9._%=-]{1,}", 
					"https:\/\/[\w\d\W\D]{1,}\.hath\.network\/[\w\d\W\D]{1,}\/[\d]{1,}\/[\w\d\W\D]{1,}\/[\w\d\W\D]{1,}\/[\w\d\W\D]{1,}\/[\w\d\W\D]{1,}\/[\w\d\W\D]{1,}"],
		"SankakuComplex": ["https:\/\/cs\.sankakucomplex\.com\/data\/[\w\d]{2}\/[\w\d]{2}\/[\w\d]{32}\.[\w\W]{3,4}\?e=[\d]{8,15}&m=[\w\d_-]{1,32}"],
		"YiffParty": ["https:\/\/data\.yiff\.party\/.*\/[\d]{1,}\/[\d]{1,}\/[\d]{1,}\/[\w\d\D\W]{1,}\.[\d\w]{2,5}",
					  "https:\/\/data\.yiff\.party\/shared_data\/[\w\d]{1,}\/[\w\d]{1,}\.[\d\w]{2,5}", 
					  "https:\/\/data\.yiff\.party\/.*\/[\d]{1,}\/[\d]{1,}\/[\w\d-]{1,}\.[\d\w]{2,5}"],
		"e621": ["https:\/\/static.\.e621\.net\/data\/..\/..\/[a-zA-Z0-9._-]{1,}"]
	}
	for reg in list(regex_list):
		for regex in regex_list[reg]:
			if re.match(regex, file):
				return reg
			else:
				continue
	return "Other"


def download_image(image, query):
	s = requests.Session()
	system.values.downloading += 1
	try:
		location = match_download_location(image['file_url'])
		original_name, file_type, filename = parse_filename(image['file_url'])
		try:
			if not os.path.isdir(f"database/{location}/"):
				os.mkdir(f"database/{location}/")
		except:
			pass
		allowed = list(system.allowed_filetypes)
		allowed.append("zip")
		if file_type.lower() in allowed:
			src = s.get(image['file_url'], headers=headers, stream=True, timeout=300, allow_redirects=True)
			image['file_url'] = src.url
			if src.status_code == 200:
				filesize = humanize.naturalsize(int(src.headers.get("content-length")))
				if system.new_print_style:
					if len(filename) > 50:
						printname = filename[:50] + "..."
					else:
						printname = filename
					system.print_queue.append(f"{colored(f'{printname}.{file_type}', 'green')} - {location} [{filesize}]")
				image_content = src.content
				try:
					if not file_type.lower() in ['webm', 'mp4', 'zip']:
						with PIL.Image.open(BytesIO(image_content)) as img:
							img.verify()
				except:
					pass
				else:
					filename = f"{system.engine.modify_filename(filename, BytesIO(image_content), location=location)}.{file_type}"
					if file_type.lower() == "zip":
						zip_file = zipfile.ZipFile(BytesIO(image_content))
						for file in zip_file.namelist():
							extension = file.split(".")[-1]
							if extension in system.allowed_filetypes:
								content = zip_file.read(file)
								filesize = humanize.naturalsize(sys.getsizeof(content))
								file = system.engine.make_safe_filename(file.split('/')[-1].replace(f".{extension}", ""))
								file_bytesio = BytesIO(content)
								filename = f"{system.engine.modify_filename(file, BytesIO(content), location=location)}.{extension}"
								if len(filename) > 50:
									printname = filename[:50] + "..."
								else:
									printname = filename
								zipmd5 = system.engine.get_md5(file_bytesio, bytesio=True)
								if os.path.isfile(f"database/{location}/{filename}"):
									if zipmd5 == system.engine.get_md5(f"database/{location}/{filename}"):
										existing_tags = system.database.read_tags(
											f"database/{location}/{filename}", location)
										if len(existing_tags) == 0:
											pass
										else:
											if not query in existing_tags:
												if 'None' in existing_tags:
													existing_tags.remove('None')
												existing_tags.append(query)
												for tag in image['tags']:
													if not tag in existing_tags:
														existing_tags.append(tag)
												system.database.update_tags(filename, location, list(set(existing_tags)))
											raise system.exceptions.DuplicateFileDownloaded
									else:
										filename = system.engine.uniquify(f"database/{location}/{filename}").split("/")[-1]
								with open(f"database/{location}/{filename}", "wb") as f:
									f.write(content)
								system.database.write_to_db(filename, location, image["sources"], image["tags"], artist=image["artist"], additional=image["additional"])
								if system.new_print_style:
									system.print_queue.append(f"{colored(f'{printname}', 'green')} - {location} [{filesize}] (From zip)")
								system.logger_queue.put(f"File: {filename} from {location} [{filesize}] (From zip file)")
					else:
						try:
							if os.path.isfile(f"database/{location}/{filename}"):
								if system.engine.get_md5(BytesIO(image_content), bytesio=True) == system.engine.get_md5(filename):
									while True:
										try:
											existing_tags = system.database.read_tags(filename, location)
										except:
											continue
										else:
											break
									if len(existing_tags) == 0:
										pass
									else:
										if not query in existing_tags:
											if 'None' in existing_tags:
												existing_tags.remove('None')
											existing_tags.append(query)
											for tag in image['tags']:
												if not tag in existing_tags:
													existing_tags.append(tag)
											system.database.update_tags(filename, location, list(set(existing_tags)))
										raise system.exceptions.DuplicateFileDownloaded
								else:
									filename = system.engine.uniquify(f"database/{location}/{filename}").split("/")[-1]
						except:
							pass
						else:
							if not query in image['tags']:
								image['tags'].append(query)
							try:
								with open(f"database/{location}/{filename}", "wb") as f:
									f.write(image_content)
								system.database.write_to_db(filename, location, image["sources"], image["tags"], artist=image["artist"], additional=image["additional"])
							except Exception as e:
								system.engine.log_exception(e)
							system.logger_queue.put(f"File: {filename} from {location} ({image['file_url']}) [{filesize}]")
		system.values.downloading -= 1
		system.values.finished += 1
	except Exception as e:
		system.values.downloading -= 1
		system.values.finished += 1
		if isinstance(e, system.exceptions.DuplicateFileDownloaded):
			system.print_queue.append(f"Duplicate File Downloaded: {colored(filename, 'cyan')}")
			pass
		else:
			system.engine.log_exception(e)


def download_controller(query, max_downloads):
	download_threadpool = ThreadPoolExecutor(max_workers=max_downloads)
	while system.values.scraping:
		time.sleep(0.01)
		for image in system.values.found:
			if image in system.values.downloaded:
				continue
			else:
				download_threadpool.submit(download_image, image, query)
				system.values.downloaded.append(image)
	while system.values.downloading > 0:
		time.sleep(1)
	while len(system.print_queue) > 0:
		time.sleep(0.5)
	system.print_queue.append(colored("Task Complete.", "red"))


def write_controller(query):
	while system.values.scraping:
		time.sleep(0.3)
		for image in system.values.found:
			if isinstance(image, list):
				image = image[0]
			if image in system.values.written:
				continue
			else:
				with open(f"database/link_lists/{query}.txt", "a+") as handle:
					handle.write(f"{image}\n")
				system.values.written.append(image)
