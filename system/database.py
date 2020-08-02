import ast
import os
import re
import sqlite3
import urllib.parse
from datetime import datetime

import progressbar
from sqlite3worker import Sqlite3Worker
from werkzeug.security import generate_password_hash

import system.title
import system.values
from scrapers import *
from system.engine import *

try:
	import ujson as json
except:
	import json

db = Sqlite3Worker('database/data.db')

def make_tags_safe(tags):
	processed_tags = list()
	for tag in tags:
		if tag == "None":
			processed_tags.append("None")
		else:
			tag = re.sub('(_{2,8})', '_', make_safe_filename(urllib.parse.unquote(tag).strip()).lower().strip())
			if len(tag.strip()) < 3:
				continue
			else:
				processed_tags.append(tag.strip())
	if "None" in processed_tags:
		if len(processed_tags) > 1:
			processed_tags.remove("None")
	return sorted(list(set(processed_tags)))


def convert_list_to_json(string):
	return string.replace("'", '"').replace(",", ", ")


def write_to_db(filename, location, source, tags, artist="Unknown", additional=dict()):
	if location == "LocalFile":
		md5 = get_md5(filename)
		filesize = os.path.getsize(filename)
	else:
		md5 = get_md5(f"database/{location}/{filename}")
		filesize = os.path.getsize(f"database/{location}/{filename}")
	meta = {
		"artist": artist,
		"sources": [],
		"timestamp": int(datetime.timestamp(datetime.now())),
		"additional": additional,
		"filesize": filesize
	}
	if isinstance(source, list):
		meta['sources'].extend(source)
	else:
		meta['sources'] = [source]
	
	db.execute('INSERT OR IGNORE INTO OnaniFiles (filename, location, "md5", tags, meta) VALUES (?, ?, ?, ?, ?)', (filename, location, md5, json.dumps(make_tags_safe(tags)), json.dumps(meta)))


def update_tags(filename, location, new_tags):
	db.execute('UPDATE OnaniFiles SET tags=? WHERE filename=? AND location=?', (json.dumps(make_tags_safe(new_tags)), filename, location))


def edit_meta(filename, location, new_meta):
	db.execute('UPDATE OnaniFiles SET meta=? WHERE filename=? AND location=?', (json.dumps(new_meta), filename, location))


def edit_filename(filename, location, new_filename):
	if os.path.isfile(f"database/{location}/{filename}"):
		extension = filename.split(".")[-1]
		parts = filename.replace(f".{extension}", "").split("-")
		parts[0] = make_safe_filename(new_filename)
		os.rename(f"database/{location}/{filename}", f"database/{location}/{'-'.join(parts)}.{extension}")
		db.execute('UPDATE OnaniFiles SET filename=? WHERE filename=? AND location=?', (f"{'-'.join(parts)}.{extension}", filename, location))
		return {"location": location, "filename": f"{'-'.join(parts)}.{extension}"}


def read_meta(filename, location):
	meta = db.execute('SELECT "meta" FROM OnaniFiles WHERE filename=? AND location=?', (filename, location))
	try:
		return json.loads(meta[0][0])
	except:
		return dict()


def read_tags(filename, location):
	tags = db.execute('SELECT "tags" FROM OnaniFiles WHERE filename=? AND location=?', (filename, location))
	try:
		return json.loads(tags[0][0])
	except:
		return list()


def delete_entry_and_file(filename, location):
	try:
		os.remove(f"database/{location}/{filename}")
	except:
		pass
	db.execute('DELETE FROM OnaniFiles WHERE filename=? AND location=?', (filename, location))


def return_md5_of_table(location):
	md5_list = list()
	for md5 in db.execute(f'SELECT "md5" FROM OnaniFiles WHERE location=?', (location, )):
		md5_list.append(md5[0])
	return md5_list


def delete_tag(tag, delete_files):
	for row in db.execute('SELECT "filename", "location", "tags" FROM OnaniFiles'):
		current_tags = json.loads(row[2])
		if tag in current_tags:
			current_tags.remove(tag)
			if len(current_tags) == 0:
				if delete_files:
					try:
						os.remove(f"database/{row[1]}/{row[0]}")
					except:
						pass
					db.execute('DELETE FROM OnaniFiles WHERE filename=? AND location=?', (row[0], row[1]))
					continue
				else:
					current_tags.append('None')
			db.execute('UPDATE OnaniFiles SET tags=? WHERE filename=? AND location=?', (json.dumps(current_tags), row[0], row[1]))


def verify_db():
	files = list()
	folders = set()
	widgets = ['[', progressbar.Timer(), '] ', progressbar.Bar(marker="█"), ' (', progressbar.ETA(), ') ']
	count = 0
	rows = db.execute('SELECT * FROM OnaniFiles')
	with progressbar.ProgressBar(max_value=len(rows), redirect_stdout=True, widgets=widgets) as bar:
		for row in rows:
			folders.add(row[1])
			if row[1] == "LocalFile":
				if not os.path.isfile(row[0]):
					db.execute('DELETE FROM OnaniFiles WHERE filename=? AND location=?', (row[0], row[1]))
					print("File Did not exist, Deleted.")
				else:
					tags = json.loads(row[3])
					new_tags = json.dumps(make_tags_safe(tags))
					meta = json.loads(row[4])
					try:
						if meta['filesize'] == "Unknown":
							meta['filesize'] = os.path.getsize(row[0])
							db.execute("UPDATE OnaniFiles SET meta=? WHERE filename=? AND location=?", (json.dumps(meta), row[0], row[1]))
					except:
						print("Meta was corrupt. Rebuilding...")
						meta = {
							"artist": "Unknown",
							"sources": ["Unknown"],
							"timestamp": int(datetime.timestamp(datetime.now())),
							"additional": dict(),
							"filesize": os.path.getsize(row[0])
						}
					files.append(row[0])
					count += 1
					bar.update(count)		
			else:
				if not os.path.isfile(f"database/{row[1]}/{row[0]}"):
					db.execute('DELETE FROM OnaniFiles WHERE filename=? AND location=?', (row[0], row[1]))
					print("File Did not exist, Deleted.")
				else:
					tags = json.loads(row[3])
					new_tags = json.dumps(make_tags_safe(tags))
					meta = json.loads(row[4])
					db.execute("UPDATE OnaniFiles SET tags=? WHERE filename=? AND location=?", (new_tags, row[0], row[1]))
					try:
						if meta['filesize'] == "Unknown":
							meta['filesize'] = os.path.getsize(f"database/{row[1]}/{row[0]}")
							db.execute("UPDATE OnaniFiles SET meta=? WHERE filename=? AND location=?", (json.dumps(meta), row[0], row[1]))
					except:
						print("Meta was corrupt. Rebuilding...")
						meta = {
							"artist": "Unknown",
							"sources": ["Unknown"],
							"timestamp": int(datetime.timestamp(datetime.now())),
							"additional": dict(),
							"filesize": os.path.getsize(f"database/{row[1]}/{row[0]}")
						}
						db.execute("UPDATE OnaniFiles SET meta=? WHERE filename=? AND location=?", (json.dumps(meta), row[0], row[1]))
					files.append(f"database/{row[1]}/{row[0]}")
					count += 1
					bar.update(count)

	for folder in list(folders):
		if os.path.isdir(f"database/{folder}/"):
			print(f"Checking {folder} Directory...")
			dir_files = os.listdir(f"database/{folder}/")
			count = 0
			with progressbar.ProgressBar(max_value=len(dir_files), redirect_stdout=True, widgets=widgets) as bar:
				for file in dir_files:
					if not f"database/{folder}/{file}" in files:
						print(f"Found Foreign File, Adding to database. ({file})")
						meta = {
							"artist": "Unknown",
							"sources": ["Unknown"],
							"timestamp": int(datetime.timestamp(datetime.now())),
							"additional": dict(),
							"filesize": os.path.getsize(f"database/{folder}/{file}")
						}
						db.execute('INSERT OR IGNORE INTO OnaniFiles (filename, location, "md5", tags, meta) VALUES (?, ?, ?, ?, ?)', (file, folder, get_md5(
							f"database/{folder}/{file}"), json.dumps(make_tags_safe(['None'])), json.dumps(meta)))
					count += 1
					bar.update(count)


def query_file_count():
	count = db.execute('SELECT COUNT(*) FROM OnaniFiles')
	return count[0]


def get_table_images():
	folders = dict()
	for row in db.execute('SELECT "filename", "location" FROM OnaniFiles'):
		try:
			folders[row[1]]
		except:
			folders[row[1]] = list()
		else:
			pass
		folders[row[1]].append(row[0])
	return folders


# Web Server
def get_tag_size():
	tags = dict()
	for row in db.execute(f'SELECT "tags" FROM OnaniFiles'):
		for tag in json.loads(row[0]):
			try:
				tags[tag]
			except:
				tags[tag] = 0
			tags[tag] += 1
	return tags


def get_files_by_tag(tag, current_user=None):
	file_list = list()
	original_tag = tag
	tags = parse_tags(tag)
	for row in db.execute(f'SELECT "filename", "location", "md5", "tags", "meta" FROM OnaniFiles'):
		if tags['all']:
			file_list.append({"location": row[1], "filename": row[0]})
			continue
		else:
			if file_search_match(row, tags, current_user):
				file_list.append({"location": row[1], "filename": row[0]})
	return {
		"name": original_tag,
		"list": file_list
	}


def list_tags():
	tags = set()
	rows = db.execute('SELECT "tags" FROM OnaniFiles')
	for row in rows:
		tags.update(json.loads(row[0]))
	return tags


def tag_count():
	tags = set()
	rows = db.execute('SELECT "tags" FROM OnaniFiles')
	for row in rows:
		tags.update(json.loads(row[0]))
	return len(tags)


def get_file_info(filename, location):
	info = db.execute('SELECT "md5", "tags", "meta" FROM OnaniFiles WHERE filename=? AND location=?', (filename, location))
	try:
		meta = json.loads(info[0][2])
		meta['md5'] = info[0][0]
		meta['tags'] = info[0][1]
		return meta
	except:
		return None


def get_random_file():
	row = db.execute('SELECT "filename", "location" FROM OnaniFiles ORDER BY RANDOM() LIMIT 1')[0]
	return {"filename": row[0], "location": row[1]}
	

def get_random_tag():
	row = db.execute('SELECT "tags" FROM OnaniFiles ORDER BY RANDOM() LIMIT 1')[0]
	return {"tag": random.choice(json.loads(row[0]))}


def get_all_files():
	files = list()
	for row in db.execute('SELECT "filename", "location" FROM OnaniFiles'):
		files.append({"filename": row[0], "location": row[1]})
	return files


def get_tables():
	folders = set()
	for row in db.execute('SELECT "location" FROM OnaniFiles'):
		folders.add(row[0])
	return list(folders)


def get_collections():
	collections = list()
	for row in db.execute('SELECT "id", "name" FROM OnaniCollections'):
		collections.append({
			"id": row[0],
			"name": row[1]
		})
	return collections


def get_collection_count():
	count = db.execute('SELECT COUNT(*) FROM OnaniCollections')
	return count[0]


# USERS

def create_user(username, password, admin=False, favourites=[], settings=system.default_user_settings):
	if len(db.execute('SELECT * FROM OnaniUsers WHERE username=? COLLATE NOCASE', (username,))) == 0:
		pass_hash, api_key = (generate_password_hash(password), create_api_key())
		db.execute('INSERT OR IGNORE INTO OnaniUsers (username, password, is_admin, api_key, favourites, settings) VALUES (?, ?, ?, ?, ?, ?)', (username, pass_hash, (1 if admin else 0), api_key, json.dumps(favourites), json.dumps(settings)))
		return {
			"username": username,
			"password": pass_hash,
			"is_admin": admin,
			"api_key": api_key,
			"favourites": favourites,
			"settings": settings
		}
	else:
		return None


def get_user(username):
	user = db.execute('SELECT * FROM OnaniUsers WHERE username=? COLLATE NOCASE', (username,))
	if not len(user) == 0:
		user = {
			"username": user[0][0],
			"password": user[0][1],
			"is_admin": (True if user[0][2] == 1 else False),
			"api_key": user[0][3],
			"favourites": json.loads(user[0][4]),
			"settings": json.loads(user[0][5])
		}
	else:
		user = None
	return user


def get_user_by_api_key(api_key):
	user = db.execute('SELECT * FROM OnaniUsers WHERE api_key=?', (api_key,))
	if not len(user) == 0:
		user = {
			"username": user[0][0],
			"password": user[0][1],
			"is_admin": (True if user[0][2] == 1 else False),
			"api_key": user[0][3],
			"favourites": json.loads(user[0][4]),
			"settings": json.loads(user[0][5])
		}
	else:
		user = None
	return user


def get_all_users():
	return_users = list()
	db_users = db.execute('SELECT "username", "is_admin", "favourites", "settings" FROM OnaniUsers')
	for user in db_users:
		return_users.append({
			"username": user[0],
			"is_admin": (True if user[1] == 1 else False),
			"favourites": json.loads(user[2]),
			"settings": json.loads(user[3])
		})
	return return_users


def update_favourites(username, favourites):
	db.execute('UPDATE OnaniUsers SET favourites=? WHERE username=?', (json.dumps(favourites), username))


def update_settings(username, settings):
	db.execute('UPDATE OnaniUsers SET settings=? WHERE username=?', (json.dumps(settings), username))


def update_api_key(username, key):
	db.execute('UPDATE OnaniUsers SET api_key=? WHERE username=?', (key, username))


def promote_user(username, is_admin):
	db.execute('UPDATE OnaniUsers SET is_admin=? WHERE username=?', ((0 if is_admin else 1), username))


def delete_user(username):
	db.execute('DELETE FROM OnaniUsers WHERE username=?', (username,))


def change_password(username, new_password):
	db.execute('UPDATE OnaniUsers SET password=? WHERE username=?', (generate_password_hash(new_password), username))


def regen_api_key(username):
	db.execute('UPDATE OnaniUsers SET api_key=? WHERE username=?', (create_api_key(), username))
