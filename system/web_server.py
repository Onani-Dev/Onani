import io
import itertools
import logging
import os
import random
import subprocess
import threading
import traceback
from datetime import timedelta
from pprint import pprint

import humanize
import psutil
import requests
from dominate import document
from dominate.tags import *
from flask import (Flask, Response, abort, flash, redirect, render_template,
                   render_template_string, request, send_file,
                   send_from_directory, url_for)
from flask_caching import Cache
from flask_cors import CORS, cross_origin
from flask_login import (
    LoginManager, UserMixin, current_user, login_required, login_user,
    logout_user)
from PIL import Image
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

import system.database
import system.download
import system.values
from system.controller import *
from system.engine import *

try:
	import ujson as json
except:
	import json


app = Flask(__name__,
			static_url_path='',
			static_folder='web/',
			template_folder='web/templates')

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = "database/OnaniUploaded/"
app.config['MAX_CONTENT_LENGTH'] = 5120 * 1024 * 1024 # 5 GB
app.config['SECRET_KEY'] = system.webviewer_secret_key
app.config['JSON_SORT_KEYS'] = False
cache = Cache()
login_manager = LoginManager()
cors = CORS(app)
login_manager.init_app(app)
cache.init_app(app, {"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 300})
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
copyright_text = p("Onani | オナニー Copyright © 2020 blakeando", style="color: #fc0303;font-size: 0.6em;text-align: center;display: block;")


def jsonify(data):
	return Response(json.dumps(data), mimetype='application/json')


def glitch_monitor():
	doc = document(title=junk_text(len=66))
	with doc.head:
		link(rel='stylesheet', href='/css/monitor.css')
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
		meta(charset="utf-8")
	with doc:
		div(_class="scanlines")
		div(_class="scanline")
		div(_class="flicker")
		div(pre(random_word_string().upper(), _class="lg"), _class="body")
	return doc.render()


def check_if_has_sinned(func):
	return (glitch_monitor if system.has_sinned else func)


class User(UserMixin): pass


@login_manager.user_loader
def user_loader(username):
	user_check = system.database.get_user(username)
	if user_check is None:
		return
	user = User()
	user.id = user_check["username"]
	user.is_admin = user_check["is_admin"]
	user.api_key = user_check["api_key"]
	user.favourites = user_check["favourites"]
	user.settings = dict(system.default_user_settings)
	user.settings.update(user_check["settings"])
	return user


@login_manager.request_loader
def request_loader(request):
	username = request.form.get('username')
	user_check = system.database.get_user(username)
	if user_check is None:
		api_key = request.headers.get('Authorization')
		if api_key:
			user_check = system.database.get_user_by_api_key(api_key)
			if user_check is not None:
				user = User()
				user.id = user_check["username"]
				user.is_admin = user_check["is_admin"]
				user.api_key = user_check["api_key"]
				user.favourites = user_check["favourites"]
				user.settings = dict(system.default_user_settings)
				user.settings.update(user_check["settings"])
				return user
			return
	else:
		user = User()
		user.id = user_check["username"]
		user.is_admin = user_check["is_admin"]
		user.api_key = user_check["api_key"]
		user.favourites = user_check["favourites"]
		user.settings = dict(system.default_user_settings)
		user.settings.update(user_check["settings"])
		user.is_authenticated = check_password_hash(user_check['password'], request.form['password']) 
		return user


def is_allowed_extension(filename):
	filepath, ext = os.path.splitext(filename)
	return (False if not ext.replace(".", "") in system.allowed_filetypes else True)


def build_image_viewer():
	doc = document(title='Onani Viewer | ...')
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/image_viewer.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		script(type='text/javascript', src="/js/jquery-3.4.1.js")
		script(type='text/javascript', src="/js/shortcut.js")
		script(type='text/javascript', src="/js/lodash.js")
		script(type='text/javascript', src="/js/moment-with-locales.js")
		script(type='text/javascript', src="/js/strftime.js")
		script(type='text/javascript', src="/js/humanize.js")
		script(type='text/javascript', src="/js/pageviewer.js")
		script(type='text/javascript', src="/js/idbkvstore.min.js")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		div(a(img(src="/img/viewertitle.png", _class="title"), href="/", id="title-href"), hr(), _class="top")
		div(a(" < ", _class="backward", style="opacity:0.6;", id="pre"),
			a(" > ", _class="forward", style="opacity:0.6;", id="next"), _class="controls", id="control-div")
		div(id="image-container")
		div(a(_class="exit-button", id="toggle-messagebox"), _class="message-box", id="message-box")
		div(div(div(a(p("Timestamp: ... (...)", id='timestamp', title='The date when this file was added'))),
			div(a(p("MD5: ...", id="md5-text"), href="/view?tag=md5:...", id='md5-link', title="View all images with this MD5 Hash")),
			div(a(p("Source: ...", id="source-text"), id='source-link', target="_blank", title="Visit the source of this file")),
			div(a(p("Filesize: ...", id='filesize', title="heh"), style="display:inline-block;"), a(p("Artist: ...", id="artist-text"), id='artist-link', title="View more from this artist", style="display:inline-block;")),
			div(a(p("Download"), id="download-button", title="Download this image.", style="display:inline-block;padding: 10px;"), a(p("Favourite", id="favourite-text", title="Toggle Favourite"), id="toggle-favourite", style="display:inline-block;padding: 10px;"), 
			a(p("Saucenao", id="saucenao-text"), id='start-saucenao', style="display:inline-block;padding: 10px;"), 
			a(p("Print"), style="display: none; background-color: #0a0a0a; border-color: #0a0a0a; hover: select", id="april-print"), id="button-container", style="width:100%;"), hr(style="display: block; margin-top: 20px;margin-bottom: 20px;"), _class="info_box", id='info-box'),
			div(id="tag-bar"), 
			div(
				hr(style="display: block;margin-top: 40px;margin-bottom: 20px;visibility:visible;"),
				a("Add Tags",id='add-tags', style="width: 25%;text-align:center"), 
				a("Edit Artist", id='edit-artist', style="width: 25%;text-align:center"),
				a("Edit Source", id='edit-source', style="width: 25%;text-align:center"),
				a("Edit Filename", id='edit-filename', style="width: 25%;text-align:center"),
				a("Delete ...", id='delete-button', style="width: 25%;text-align:center"),
				hr(style="display: block; margin-top: 20px;margin-bottom: 20px;"), id='options-bar'), 
			_class="sidenav")
		button(">>", id="toggle-navbar")
		div(hr(), copyright_text, _class="bottom")
	return doc.render()


def build_error(code, error):
	doc = document(title=f'Onani | {code}')
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/error.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		link(rel='stylesheet', href='/css/bloody.css')
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		div(a(img(src="/img/viewertitle.png", _class="title"), href="/", id="home"), hr(), _class="top")
		div(p(str(error).split(":")[0],style="font-family: 'Bloody';font-weight: normal;font-style: normal;background: -webkit-linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(255, 0, 0, 1) 100%);-webkit-background-clip: text;-webkit-text-fill-color: transparent;font-size:2.1em;"),
		    p(str(error).split(":")[1].strip(), style="color:red;"),
			a(img(src=f"/img/error/disgust{random.randint(1,12)}.png"), href="/fun"),
			p("What?", size="4"), _class="error-box")
		div(hr(), copyright_text, _class="bottom")
	return doc.render()


@app.route('/login', methods=['GET', 'POST'])
@check_if_has_sinned
def login():
	if request.method == 'GET':
		doc = document(title='Onani | Login')
		with doc.head:
			link(rel='stylesheet', href='/css/onani-viewer.style.css')
			link(rel='stylesheet', href='/css/mainpage.style.css')
			link(rel='icon', type='image/png', href="/img/favicon.png")
			link(rel='stylesheet', href='/css/bloody.css')
			script(type='text/javascript', src="/js/jquery-3.4.1.js")
			script(type='text/javascript', src="/js/loginpage.js")
			script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
			meta(charset="utf-8")
			meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
		with doc:
			div(a(img(src="/img/viewertitle.png", _class="title"),
						href="/", id="home"), hr(), _class="top")
			div(
				p("Login", style="position:absolute;left: 25%;right: 25%;margin-top: 30px;font-family:'Bloody';font-weight: normal;font-style: normal;top: 0;background: -webkit-linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(255, 0, 0, 1) 100%);-webkit-background-clip: text;-webkit-text-fill-color: transparent;font-size:2.1em;"),
				form(
					input_(type='text', name='username', id='username',
						placeholder='Username', autocapitalize="off"),
					input_(type='password', name='password', id='password',
						autocomplete="current-password", placeholder='Password'),
					input_(type='button', name='submit', id='submit', value="Login")),
				_class="login-box")
			div(hr(), copyright_text, _class="bottom")
		return doc.render()
	else:
		username = request.form['username']
		user_check = system.database.get_user(username)
		if user_check is None:
			return redirect("/login")
		if check_password_hash(user_check['password'], request.form['password']):
			user = User()
			user.id = user_check["username"]
			user.is_admin = user_check["is_admin"]
			user.api_key = user_check["api_key"]
			user.favourites = user_check["favourites"]
			user.settings = dict(system.default_user_settings)
			user.settings.update(user_check["settings"])
			login_user(user, duration=timedelta(days=60), remember=True)
			return redirect("/")
		else:
			return redirect("/login")


@app.route("/logout")
@check_if_has_sinned
@login_required
def logout():
	logout_user()
	return redirect("/login")


@app.route('/profile')
@check_if_has_sinned
@login_required
def user_profile():
	doc = document(title=f'Onani | {current_user.id}\'s Profile')
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/mainpage.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		link(rel='stylesheet', href='/css/bloody.css')
		script(type='text/javascript', src="/js/jquery-3.4.1.js")
		script(type='text/javascript', src="/js/profile.js")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		div(a(img(src="/img/viewertitle.png", _class="title"), href="/", id="title-href"), hr(), _class="top")
		div(p(f"{current_user.id}{' (Admin)' if current_user.is_admin else ''}", id="logged-in-text"),
			hr(style="margin-top:5px;margin-bottom:20px;"),
			label("Api Key:", _for="api-key"),
			input_(value=current_user.api_key, readonly="", id="api-key"),
			button("Copy", id="copy-button"), button("Regenerate", id="regen-button"), hr(style="margin-top:20px;"),
			a(p(f"{len(current_user.favourites)} Favourite{'s' if len(current_user.favourites) != 1 else ''}", id="favourite-count"), href="/view?tag=Favourites"),
			hr(),
			p("Settings:"),
			label("Free Hand:", title="Hand you don't fap with ;)", _for="free-hand"),
			select((option("left", value="left", selected="selected") if current_user.settings['free_hand'] == "left" else option("left", value="left")), 
                    (option("right", value="right", selected="selected") if current_user.settings['free_hand'] == "right" else option("right", value="right")), id="free-hand", name="free-hand", title="Hand you don't fap with ;)"),
			label("SFW Mode:", title="fr don't know why you'd even enable this", _for="sfw-mode"),
			select((option("Enabled", value="Enabled", selected="selected") if current_user.settings['sfw_mode'] else option("Enabled", value="Enabled")),
                    (option("Disabled", value="Disabled", selected="selected") if not current_user.settings['sfw_mode'] else option("Disabled", value="Disabled")), id="sfw-mode", name="sfw-mode", title="fr don't know why you'd even enable this"),
			label("Title Splash text:", title="hahaha minecraft splash text", _for="splash-text"),
			select((option("Enabled", value="Enabled", selected="selected") if current_user.settings['splash_text'] else option("Enabled", value="Enabled")),
                    (option("Disabled", value="Disabled", selected="selected") if not current_user.settings['splash_text'] else option("Disabled", value="Disabled")), id="splash-text", name="splash-text", title="hahaha minecraft splash text"),
			button("Save Changes", id="save-button"),
			_class="red-page")
		div(hr(), copyright_text, _class="bottom")
	return doc.render()


@app.route('/')
@check_if_has_sinned
@login_required
def send_index():
	doc = document(title=f'Onani Viewer (Version {system.__version__})')
	with doc.head:
		comment('There is not enough memory.')
		comment('            - My PSP, 2020')
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/mainpage.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		link(rel='stylesheet', href='/css/jquery.flexdatalist.css')
		script(type='text/javascript', src="/js/jquery-3.4.1.js")
		script(type='text/javascript', src="/js/jquery.flexdatalist.js")
		script(type='text/javascript', src="/js/gauge.js")
		script(type='text/javascript', src="/js/shortcut.js")
		script(type='text/javascript', src="/js/idbkvstore.min.js")
		script(type='text/javascript', src="/js/mainpage.js")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		title_image = div(a(img(src="/img/viewertitle.png", _class="title"), href="/", id="home"), _class="title_image")
		if current_user.settings["splash_text"]:
			title_image.add(p(random.choice(system.splashes), id="subtitle"))
		p(f"Onani v{system.__version__}",style="color: #fc0303;display: block;text-align: center;font-size: 0.5em;")
		navbar = div(
			div(
				button("Images", i(_class="fa fa-caret-down"), _class="dropbtn"),
				div(
					a("View All Images (...)", href="/view", id="image_count"),
					a("View All Tags (...)", href="/all_tags", id="tag_count"),
					a("Random Tag", id="view-random",
					  style="cursor:pointer;", _class="dropdown-item"),
					a("Random Image", id="view-random-image", style="cursor:pointer;", _class="dropdown-item"),
					a("Sites", id="toggle-sites", style="cursor:pointer;", _class="dropdown-item"),
				_class="dropdown-content"),
			 _class="dropdown"),
			div(
				button("Tools", i(_class="fa fa-caret-down"), _class="dropbtn"),
				div(
					a("Uploader", id="toggle-uploader", style="cursor:pointer;", _class="dropdown-item"),
					# a("Scraper", href="/scraper", style="cursor:pointer;", _class="dropdown-item"), Disabled for the moment
					a("Stats", id="toggle-stats", style="cursor:pointer;", _class="dropdown-item"),
				_class="dropdown-content"),
			 _class="dropdown"),
			div(
				button(current_user.id, i(_class="fa fa-caret-down"), _class="dropbtn"),
				div(
					a("Profile", href="/profile", id="open-profile", style="cursor:pointer;", _class="dropdown-item"),
					a("Favourites", id="view-favourites", style="cursor:pointer;", _class="dropdown-item"),
					a("Logout", id="logout-user", style="cursor:pointer;", _class="dropdown-item"),
				_class="dropdown-content"),
			 _class="dropdown"),
		_class="navbar")
		
		if request.args.get("zone") == "cum":
			navbar.add(a("cum", href="/cum"))
			audio(autoplay="true", loop="true", hidden="true", src="/audio/welcome.mp3", id="autoplay_audio")
		div(hr())
		div(
			div(form(input_(type="text", list="tags", name="tag", placeholder="Tags...", _class="flexdatalist", spellcheck="false", autocapitalize="off", multiple='multiple', data_min_length='1', id="search-box"),
				datalist(id="tags")), _class="search-text-input"), div(a("Search", _class="submit-button", id="search-submit-button"), _class="search-submit-div"), _class="search_box")
		div(a(id="upload-exit-button", _class="exit-button", style="cursor:pointer;"),
			p("Select Files to upload.", style="color: #fc0303"),
			input_(type="file", name="file", multiple="true", id="selected-files"),
			input_(type="text", name="tags", placeholder="Tags (Split by spaces)", _class="data-input", id="data-tags"),
			input_(type="text", name="source", placeholder="Source", _class="data-input", id="data-sources"),
			input_(type="text", name="artist", placeholder="Artist", _class="data-input", id="data-artist"),
			button("Upload", id="upload-button"), _class="message-box large-padding", id="uploader-box")
		div(a(id="site-exit-button", _class="exit-button", style="cursor:pointer;"),
		    _class="message-box large-padding", id="site-box", style="max-height:500px;")
		div(a(id="dir-exit-button", _class="exit-button", style="cursor:pointer;"),
		    _class="message-box small-padding", id="dir-box", style="height:600px;width:600px;overflow-y:scroll;")
		div(a(id="stats-exit-button", _class="exit-button", style="cursor:pointer;"),
			div(div(p('CPU Usage'), canvas(id='cpu-gauge'), p(id='cpu-value'), _class="gauge-container"), 
				div(p("RAM Usage"), canvas(id='ram-gauge'), p(id='ram-value'), _class="gauge-container"), 
				div(p("Disk Usage"), canvas(id='disk-gauge'), p(id='disk-value'), _class="gauge-container")), a("More stats", href="/server_stats", style="text-decoration: underline", id="full-stats"), _class="message-box small-padding", id="stat-box")
		div(id="don1")
		div(id="don2")
		div(id='drum')
		div(id='don-left')
		div(id='don-right')
		div(id='ka-left')
		div(id='ka-right')
		div(hr(), copyright_text, _class="bottom")

	return doc.render()


@app.route('/view')
@check_if_has_sinned
@login_required
def send_viewer():
	doc = document(title='Onani Viewer | ...')
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/images.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		script(type='text/javascript', src="/js/jquery-3.4.1.js")
		script(type='text/javascript', src="/js/shortcut.js")
		script(type='text/javascript', src="/js/lodash.js")
		script(type='text/javascript', src="/js/imagepage.js")
		script(type='text/javascript', src="/js/idbkvstore.min.js")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		header = div(_class="top", id="topbar")
		header.add(a(img(src="/img/viewertitle.png", _class="Title"), href="/"))
		header.add(
				div(
					a(" << ", _class="backward", id="pre_firstpage"),
					a(" < ", _class="backward", id="pre"),
					form(
						input_(list="tags", name="tag", type="text", placeholder="Search Tags...", value="", _class="search", spellcheck="false", autocapitalize="off", id="search_box"), action="/view", method="get"),
						a(" > ", _class="forward", id="next"), 
						a(" >> ", _class="forward", id="next_lastpage"),
					_class="controls"))
		header.add(
				div(
					a("⇄", _class="reverse disabled", id="reverse"), 
					a("Sort", _class="sort disabled", id="sort"), 
					a(div(id="magnifying-glass"), _class="jump disabled", id="jumpe"),
				 _class="sort_controls"))
		header.add(hr())
		div(
			div(
				div(),
				div(),
				div(),
			_class="loading"),
		_class="loading-container", id="loading-container")
		div(
			p("Amount of images: ...", id="image_amount"), 
			p("Images on page: ...", id="images_on_page"),
			p("../..", id="page-counter"),
		_class="info_box")
		container = div(
						div(_class="column", id="column1"),
						div(_class="column", id="column2"),
						div(_class="column", id="column3"),
						div(_class="column", id="column4"),
						div(_class="column", id="column5"),
						div(_class="column", id="column6"), 
					_class="row")
		div(hr(), copyright_text, _class="bottom")
	return doc.render()


@app.route('/all_tags')
@check_if_has_sinned
@login_required
def send_all_tags():
	doc = document(title='Onani Viewer | All Tags')
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/tags.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		script(type='text/javascript', src="/js/jquery-3.4.1.js")
		script(type='text/javascript', src="/js/tagpage.js")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		div(a(img(src="/img/viewertitle.png", _class="title"), href="/", id="home"), hr(), _class="top")
		div(div(div(), div(), div(), _class="loading"),
		    _class="loading-container", id="loading-container")
		div(hr(), copyright_text, _class="bottom")
		div(_class="tags", id="tags_div")
	return doc.render()


@app.route("/server_stats")
@check_if_has_sinned
@login_required
def send_stats():
	doc = document(title='Onani | Server Stats')
	disk = psutil.disk_usage(os.getcwd())
	tables = system.database.get_table_images()
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/stats.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		div(a(img(src="/img/viewertitle.png", _class="title"), href="/", id="home"), hr(), _class="top")
		container = div()
		container += h1("Disk Status:")
		container += p(f"{humanize.naturalsize(disk.total)} Total Disk Space")
		container += p(f"{humanize.naturalsize(disk.free)} Disk Space Free")
		container += p(f"{humanize.naturalsize(disk.used)} disk space used. ({round(disk.percent, 2)}%)")
		container += span(style="display: block; height: 40px;")
		container += h1("Onani Info:")
		container += p(f"Version: {system.__version__}")
		container += p(f"Database Size (data.db): {humanize.naturalsize(os.path.getsize('database/data.db'))}")
		image_count = 0
		for table in list(tables):
			image_count += len(tables[table])
		container += p(f"Files recorded in Database: {humanize.intcomma(image_count)}")
		container += p(f"Rank: {system.engine.presence_rank(image_count)}")
		container += p(f"Uptime: {timedelta(seconds=int(time.time()) - int(system.uptime))}")
		container += span(style="display: block; height: 40px;")
		container += h1("DB Table Info:")
		for table in list(tables):
			container += p(
				f"{table} File Count: {humanize.intcomma(len(tables[table]))}")
		container += span(style="display: block; height: 40px;")
		div(hr(), copyright_text, _class="bottom")
	return doc.render()


@app.route('/view_image')
@check_if_has_sinned
@login_required
def view_image():
	try:
		location, filename = (request.args.get("location"), request.args.get("filename"))
		if location == "LocalFile":
			pass
		else:
			filename = f'../database/{location}/{filename}'
		if request.args.get("thumb") is None:
			if request.args.get("raw") == "True":
				return send_file(filename, as_attachment=False)
			elif request.args.get("download") == "True":
				return send_file(filename, as_attachment=True)
			else:
				return build_image_viewer()
		elif request.args.get("thumb") == "True":
			if location == "LocalFile":
				thumbfile = f"system/web/thumbs/{system.engine.make_safe_filename(os.path.splitext(filename)[0])}.jpg"
			else:
				thumbfile = f"system/web/thumbs/{os.path.splitext(os.path.basename(filename))[0]}.jpg"
			if not os.path.isfile(thumbfile):
				if not os.path.isdir("system/web/thumbs"):
					os.mkdir("system/web/thumbs")
				if filename.split(".")[-1] in ['webm', 'mp4']:
					try:
						subprocess.check_output(['ffmpeg', '-i', filename.replace("../", ""), '-ss', '00:00:00.000', '-vframes', '1', thumbfile, '-y'], stderr=subprocess.DEVNULL)
					except Exception as e:
						log_exception(e)
						return send_file('../system/web/img/video_default.png', as_attachment=False)
				else:
					try:
						im = Image.open(filename.replace("../", ""))
						im.thumbnail((530, 530), Image.ANTIALIAS)
						im.convert('RGB').save(thumbfile, format='JPEG')
					except Exception as e:
						log_exception(e)
						return send_file('../system/web/img/missing.png', as_attachment=False)
			return redirect(thumbfile.replace("system/web", ""))
	except Exception as e:
		log_exception(e)
		abort(404)


@app.route("/cum")
@check_if_has_sinned
def cum():
	doc = document(title='Consuming Cum')
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/egg.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		script(type='text/javascript', src="/js/jquery-3.4.1.js")
		script(type='text/javascript', src="/js/timer.js")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		audio(autoplay="true", loop="true", hidden="true", src="/audio/cumcumcum.mp3", id="autoplay_audio")
		img(src="/img/cum.gif")
		a(id="timer")
	return doc.render()


@app.route("/fun")
def hell_page():
	doc = document(title=junk_text(len=36))
	with doc.head:
		link(rel='stylesheet', href='/css/fun.css')
		link(rel='icon', type='image/png', href="/img/sonic_fun_is_infinite.png")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
	with doc:
		audio(autoplay="true", loop="true", hidden="true", src=("/audio/fun_is_infinite.mp3" if random.randint(1, 8) != 1 else "/audio/work_that_sucker_to_death.mp3"), id="autoplay_audio")
		div(h1("たのしさ∞"), h1("セガ・エンタープライゼス"), _class="center")
		div(h1("まぢん　画"), _class="bottomright")
	return doc.render(), 666


@app.route('/scraper')
@check_if_has_sinned
@login_required
@cross_origin()
def scraper():
	doc = document(title='Onani Scraper')
	with doc.head:
		link(rel='stylesheet', href='/css/onani-viewer.style.css')
		link(rel='stylesheet', href='/css/mainpage.style.css')
		link(rel='icon', type='image/png', href="/img/favicon.png")
		link(rel='stylesheet', href='/css/jquery.flexdatalist.css')
		script(type='text/javascript', src="/js/jquery-3.4.1.js")
		script(type='text/javascript', src="/js/ansi_up.js")
		script(type='text/javascript', src="/js/scraper.js")
		script(src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js", crossorigin="anonymous")
		meta(charset="utf-8")
		meta(name="viewport", content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1")
	with doc:
		div(a(img(src="/img/onani.png", _class="title"), href="/"),
		    div(a("Scrape", id="toggle-scraper-menu", style="cursor:pointer;"), a("Download", id="toggle-downloader-menu", style="cursor:pointer;"), a("Output Console", id="toggle-console", style="cursor:pointer;"),  _class="navbar"), hr(), _class="top")
		div(form(id="sites-selectors"), id="pannel-menu", _class="message-box", autocomplete="off", style="display:block;width:500px;overflow-y: hidden;")
		div(a(id="exit-console-button", _class="exit-button", style="cursor:pointer;"), id="console-pannel",
		    _class="message-box", style="word-wrap:break-word;white-space:pre-wrap;width:500px;height:500px;font-family:\"Consolas\";z-index: 4;text-align: left;font-size:12px;color: white;")
		div(hr(), copyright_text, _class="bottom")

	return doc.render()


@app.route("/rokurokuroku")
def rokurokuroku():
	return glitch_monitor(), 666


# API
@cache.cached(timeout=500, key_prefix='Onani:Counts')
def counts_(request):
	if request.method == "GET":
		return jsonify({
			"tag_count": system.database.tag_count(),
			"image_count": system.database.query_file_count(),
			"collection_count": system.database.get_collection_count()
        })
	else:
		abort(405)

def tag_counts_(request):
	if request.method == "GET":
		try:
			start, limit = ((postive_num((int(request.args.get("start")) if request.args.get("start") is not None else 0))),
			                (postive_num((int(request.args.get("limit")) if request.args.get("limit") is not None else 500)))
							)
		except:
			abort(400)
		if cache.get("tag_counts") is None:
			tag_counts = system.database.get_tag_size()
			cache.set("tag_counts", tag_counts)
		else:
			tag_counts = cache.get("tag_counts")
		next_tags = dict(zip(list(tag_counts.keys())[(start):(start + limit)], list(tag_counts.values())[(start):(start + limit)]))
		return jsonify({
			"total": len(tag_counts),
			"start_next": (start + limit if len(next_tags) == limit else None),
			"tags": next_tags
			})
	else:
		abort(405)


def query_tags_(request):
	if request.method == "GET":
		tag, directory = (request.args.get("tag"), request.args.get("directory"))
		try:
			start, limit = (
				(postive_num((int(request.args.get("start")) if request.args.get("start") is not None else 0))), 
				(postive_num((int(request.args.get("limit")) if request.args.get("limit") is not None else 15000)))
				)
		except:
			abort(400)
		if tag is None:
			if directory is not None:
				if cache.get(directory) is None:
					files = system.engine.get_directory_files(directory)
					cache.set(directory, files)
				else:
					files = cache.get(directory)
			else:
				if cache.get("all") is None:
					files = system.database.get_files_by_tag("all")
					cache.set("all", files)
				else:
					files = cache.get("all")
		else:
			if cache.get(tag) is None:
				files = system.database.get_files_by_tag(tag, current_user=current_user)
				if not "Favourites" in tag.split(" "):
					cache.set(tag, files)
			else:
				files = cache.get(tag)
		next_files = files['list'][(start):(start + limit)]
		return jsonify({
			"name": files['name'],
			"total": len(files['list']),
			"start_next": (start + limit if len(next_files) == limit else None),
			"files": next_files
		})
	else:
		abort(405)


def image_(request):
	if request.method == 'GET':
		if cache.get(request.args.get("filename") + request.args.get("location")) is None:
			fileinfo = system.database.get_file_info(request.args.get("filename"), request.args.get("location"))
			cache.set(request.args.get("filename") + request.args.get("location"), fileinfo)
		else:
			fileinfo = cache.get(request.args.get("filename") + request.args.get("location"))
			fileinfo['tags']
		if fileinfo is not None:
			return jsonify({
				"md5": fileinfo['md5'],
				"timestamp": fileinfo['timestamp'],
				"filesize": fileinfo['filesize'],
				"source": fileinfo['sources'],
				"artist": fileinfo['artist'],
				"additional": fileinfo['additional'],
				"tags": (json.loads(fileinfo['tags']) if isinstance(fileinfo['tags'], str) else fileinfo['tags']),
				"favourite": ({"location": request.args.get("location"), "filename": request.args.get("filename")} in current_user.favourites),
				"readonly": opposite_bool(current_user.is_admin)
			})
		else:
			abort(404)

	elif request.method == "DELETE":
		if current_user.is_admin:
			args = request.get_json(force=True, silent=True)
			fileinfo = system.database.get_file_info(args["filename"], args["location"])
			if fileinfo is not None:
				system.database.delete_entry_and_file(args["filename"], args["location"])
				return '', 204
			else:
				abort(404)
		else:
			abort(403)
	else:
		abort(405)


def tags_(request):
	if request.method == "GET":
		try:
			start, limit = ((postive_num((int(request.args.get("start")) if request.args.get("start") is not None else 0))),
			                (postive_num((int(request.args.get("limit")) if request.args.get("limit") is not None else 10000)))
							)
		except:
			abort(400)
		if cache.get("ONANI:TAGS") is None:
			tag_counts = system.database.list_tags()
			cache.set("ONANI:TAGS", tag_counts)
		else:
			tag_counts = cache.get("ONANI:TAGS")
		next_tags = list(tag_counts)[start:start + limit]
		return jsonify({
			"total": len(tag_counts),
			"start_next": (start + limit if len(next_tags) == limit else None),
			"tags": next_tags
			})

	elif request.method == "PUT":
		if current_user.is_admin:
			args = request.get_json(force=True, silent=True)
			existing = system.database.read_tags(args["filename"], args["location"])
			existing.extend(args["tags"])
			system.database.update_tags(args["filename"], args["location"], existing)
			args['tags'] = sorted(existing)
			if cache.get(args["filename"]) is None:
				pass
			else:
				fileinfo = cache.get(args["filename"])
				fileinfo["tags"] = sorted(existing)
				cache.set(args["filename"], fileinfo)
			return jsonify(args), 202
		else:
			abort(403)

	elif request.method == "DELETE":
		if current_user.is_admin:
			args = request.get_json(force=True, silent=True)
			existing = system.database.read_tags(args["filename"], args["location"])
			for tag in args['tags']:
				try:
					existing.remove(tag)
				except:
					pass
			system.database.update_tags(args["filename"], args["location"], existing)
			args['tags'] = sorted(existing)
			if cache.get(args["filename"]) is None:
				pass
			else:
				fileinfo = cache.get(args["filename"])
				fileinfo["tags"] = sorted(existing)
				cache.set(args["filename"], fileinfo)
			return jsonify(args), 202
		else:
			abort(403)
	else:
		abort(405)


def artist_(request):
	if request.method == "GET":
		meta = system.database.read_meta(request.args.get(
		    "filename"), request.args.get("location"))
		try:
			return jsonify([meta["artist"]])
		except:
			abort(400)

	elif request.method == "PATCH":
		if current_user.is_admin:
			args = request.get_json(force=True, silent=True)
			location = args["location"]
			filename = args["filename"]
			new_artist = args["artist"]
			new_meta = system.database.read_meta(filename, location)
			new_meta["artist"] = new_artist.replace(" ", "_")
			system.database.edit_meta(filename, location, new_meta)
			if cache.get(filename + location) is None:
				pass
			else:
				fileinfo = cache.get(filename + location)
				fileinfo["artist"] = new_artist
				cache.set(filename, fileinfo)
			return jsonify(new_meta)
		else:
			abort(403)
	else:
		abort(405)


def source_(request):
	if request.method == "GET":
		meta = system.database.read_meta(request.args.get("filename"), request.args.get("location"))
		try:
			return jsonify(meta["source"])
		except:
			abort(400)

	elif request.method == "PATCH":
		if current_user.is_admin:
			args = request.get_json(force=True, silent=True)
			location = args["location"]
			filename = args["filename"]
			new_source = args["source"]
			new_meta = system.database.read_meta(filename, location)
			if "Unknown" in new_meta["sources"]:
				new_meta["sources"].remove("Unknown")
			new_meta["sources"].insert(0, new_source)
			system.database.edit_meta(filename, location, new_meta)
			if cache.get(filename + location) is None:
				pass
			else:
				fileinfo = cache.get(filename + location)
				fileinfo["sources"].insert(0, new_source)
				cache.set(filename, fileinfo)
			return jsonify(new_meta)
		else:
			abort(403)

	elif request.method == "DELETE":
		if current_user.is_admin:
			args = request.get_json(force=True, silent=True)
			location = args["location"]
			filename = args["filename"]
			remove = args["source"]
			new_meta = system.database.read_meta(filename, location)
			new_meta["sources"].remove(remove)
			system.database.edit_meta(filename, location, new_meta)
			if cache.get(filename + location) is None:
				pass
			else:
				fileinfo = cache.get(filename + location)
				fileinfo["source"].remove(remove)
				cache.set(filename, fileinfo)
			return jsonify(new_meta)
		else:
			abort(403)
	else:
		abort(405)

def saucenao_(request):
	if request.method == "POST":
		args = request.get_json(force=True, silent=True)
		location = args["location"]
		filename = args["filename"]
		if location == "LocalFile":
			filepath = filename
		else:
			filepath = f"database/{location}/{filename}"
		sauce = check_sauce(filepath)
		sauce_string = str()
		for data in sauce:
			sauce_string += str(p(data['data']['content'][0]))
			sauce_string += str(p(data['data']['title']))
			sauce_string += str(p("\nURLs:\n"))
			for url in data['data']['ext_urls']:
				sauce_string += str(a(p(url, style="color: crimson;"),
									target="_blank", rel="noopener noreferrer", href=url))
			if len(data['data']['ext_urls']) == 0:
				sauce_string += str(p("None"))
			sauce_string += str(span(style="display: block; height: 20px;"))
		if len(sauce_string) == 0:
			sauce_string += str(p("Sorry Nothing"))
		return jsonify({"html": sauce_string})
	else:
		abort(405)


def stats_(request):
	if request.method == "GET":
		ram_usage = psutil.virtual_memory()
		disk_usage = psutil.disk_usage(os.getcwd())
		return jsonify({
			"cpu": {
				"percent": psutil.cpu_percent()
			},
			"ram": {
				"percent": ram_usage.percent,
				"used": ram_usage.used,
				"free": ram_usage.free,
				"total": ram_usage.total
			},
			"disk": {
				"percent": round(disk_usage.percent, 2),
				"used": disk_usage.used,
				"free": disk_usage.free,
				"total": disk_usage.total
			},
			"onani": {
				"version": system.__version__,
				"datadb_size": os.path.getsize('database/data.db')
			}
		})
	else:
		abort(405)


@cache.cached(timeout=60, key_prefix='Onani:Sites_Cache')
def sites_(request):
	if request.method == "GET":
		return jsonify(list(system.database.get_table_images()))
	else:
		abort(405)

def login_(request):
	if request.method == "POST":
		args = request.get_json(force=True, silent=True)
		username = args['username']
		user_check = system.database.get_user(username)
		if user_check is None:
			return jsonify({"error": "Invalid Username"})
		if check_password_hash(user_check['password'], args['password']):
			user = User()
			user.id = user_check["username"]
			user.is_admin = user_check["is_admin"]
			user.api_key = user_check["api_key"]
			user.favourites = user_check["favourites"]
			user.settings = dict(system.default_user_settings)
			user.settings.update(user_check["settings"])
			login_user(user, duration=timedelta(days=60), remember=True)
			del user_check['password']
			user_check["error"] = None
			return jsonify(user_check)
		else:
			return jsonify({"error": "Invalid Password"})
	else:
		abort(405)


def profile_(request):
	if request.method == "GET":
		return jsonify({
			"username": current_user.id,
			"is_admin": current_user.is_admin,
			"api_key": current_user.api_key,
			"favourites": current_user.favourites,
			"settings": current_user.settings
		})

	elif request.method == "PUT":
		args = request.get_json(force=True, silent=True)
		image = {"location": args["location"], "filename": args["filename"]}
		if not image in current_user.favourites:
			current_user.favourites.append(image)
		system.database.update_favourites(current_user.id, current_user.favourites)
		return jsonify(current_user.favourites)
	
	elif request.method == "DELETE":
		args = request.get_json(force=True, silent=True)
		image = {"location": args["location"], "filename": args["filename"]}
		try:
			current_user.favourites.remove(image)
		except:
			pass
		else:
			system.database.update_favourites(current_user.id, current_user.favourites)
		return jsonify(current_user.favourites)

	elif request.method == "PATCH":
		args = request.get_json(force=True, silent=True)
		updated = dict(current_user.settings)
		for update in list(args["updated"]):
			updated[update] = args["updated"][update]
		current_user.settings = updated
		system.database.update_settings(current_user.id, current_user.settings)
		return jsonify(current_user.settings)


def random_(request):
	if request.method == "GET":
		if request.args.get("type") is not None:
			if request.args.get("type") == "image":
				return jsonify(system.database.get_random_file())
			elif request.args.get("type") == "tag":
				return jsonify(system.database.get_random_tag())
			else:
				abort(400)
		else:
			abort(400)


def upload_(request):
	if request.method == 'POST':
		if 'file' not in request.files:
			abort(400)
		file = request.files['file']
		if file.filename == '':
			abort(400)
		tags = json.loads(request.form.get('tags'))
		if tags is None:
			tags = ['None']
		elif len(tags) == 0:
			tags = ['None']
		try:
			if tags[0] == "":
				tags = ["None"]
		except:
			pass
		artist = request.form.get('artist')
		if artist is None:
			artist = "Unknown"
		elif len(artist) ==  0:
			artist = "Unknown"
		sources = json.loads(request.form.get('sources'))
		if sources is None:
			sources = ['Unknown']
		elif len(sources) == 0:
			sources = ["Unknown"]
		try:
			if sources[0] == "":
				sources = ["Unknown"]
		except:
			pass
		additional = json.loads(request.form.get('additional'))
		if additional is None:
			additional = {}
		additional['uploaded_by'] = current_user.id
		if file and is_allowed_extension(file.filename):
			file_bytes = file.read()
			filepath = f'{uniquify(modify_filename(secure_filename(file.filename.split(".")[0]), io.BytesIO(file_bytes), location="OnaniUploaded"))}.{file.filename.split(".")[-1]}'
			with open(f"database/OnaniUploaded/{filepath}", "wb") as f:
				f.write(file_bytes)
			system.database.write_to_db(filepath, "OnaniUploaded", sources, tags, artist=artist, additional=additional)
			return jsonify({"location": "OnaniUploaded", "filename": filepath})


def filename_(request):
	if request.method == 'PATCH':
		if current_user.is_admin:
			args = request.get_json(force=True, silent=True)
			new_filename = system.database.edit_filename(args['filename'], args['location'], args['new_filename'])
			return jsonify({"new_filename": new_filename})
		else:
			abort(401)
	else:
		abort(405)


def api_key_(request):
	if request.method == 'GET':
		return jsonify({"api_key": current_user.api_key})
	elif request.method == 'PATCH':
		new_key = create_api_key()
		system.database.update_api_key(current_user.id, new_key)
		return jsonify({"new_key": new_key})
	else:
		abort(405)


# def ua_(request):
# 	print(request.headers.get("User-Agent"))
# 	return request.headers.get("User-Agent")


@app.route("/api")
@app.route("/api/<endpoint>", methods=["GET", "POST", "DELETE", "PATCH", "PUT"])
@check_if_has_sinned
def api_v1(endpoint=None):
	if not current_user.is_authenticated:
		if not endpoint == "login":
			return jsonify({"error": "Not authenticated."}), 401
	if system.api_debug:
		print(request.method, endpoint, request.remote_addr)
	if endpoint is None:
		return jsonify({
			'api_version': 1,
			'onani_version': system.__version__,
			'db_version': system.db_version
		})
	func = {
		"counts": counts_,
		"tag_counts": tag_counts_,
		"query_tags": query_tags_,
		"image": image_,
		"tags": tags_,
		"artist": artist_,
		"source": source_,
		"saucenao": saucenao_,
		"stats": stats_,
		"sites": sites_,
		"login": login_,
		"profile": profile_,
		"random": random_,
		"upload": upload_,
		"filename": filename_,
		"api_key": api_key_
	}.get(endpoint, lambda e: abort(404))
	try:
		return func(request)
	except Exception as e:
		try:
			name = e.name
			code = e.code
		except:
			name = str(e)
			code = 500
			if system.api_debug:
				print(''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))
			log_exception(e)
		return jsonify({"error": name, "code": code}), code


# Error handlers
@app.errorhandler(401)
def error401(e):
	return redirect("/login")


@app.errorhandler(404)
def error404(e):
	return build_error(404, e), 404


@app.errorhandler(405)
def error405(e):
	return build_error(405, e), 405


@app.errorhandler(500)
def error500(e):
	return build_error(500, e), 500

def start_web_viewer():
	app.run(host="0.0.0.0", port=system.web_viewer_port, threaded=True)


# regs = {
# 	'(http[s]?:\/\/)?(e-hentai\.org)\/(g)\/([0-9]{1,9})\/([a-zA-Z0-9]{1,10})\/?': "ehentai",
# 	'(http[s]?:\/\/)?(yiff\.party)\/patreon\/([\d]{7,12})': "yiffparty",
# 	'((http[s]?:\/\/)?twitter\.com\/([\w\d]{1,})|@([\w\d]{1,}))': "twitter"
# }
