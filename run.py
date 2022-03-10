# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-10 17:17:12
import random
import string
from datetime import datetime, timedelta

import click

from Onani import db, init_app
from Onani.controllers import create_user
from Onani.models import Ban, Tag, User
from Onani.models.news import NewsPost
from Onani.models.tag import TagType
from Onani.models.user import UserPermissions

app = init_app()


def random_user() -> User:
    pfps = [
        "/static/image/armagan.gif",
        "/static/image/default.png",
        "/static/image/dirt.gif",
        "/static/image/looking.png",
        "/static/image/sonic_fun.png",
    ]
    user = create_user(
        username="".join([random.choice(string.ascii_letters) for _ in range(8)]),
        password="Onani1",
    )
    user.settings.avatar = random.choice(pfps)
    return user


def random_tag() -> Tag:
    tagtypes = [
        TagType.ARTIST,
        TagType.BANNED,
        TagType.CHARACTER,
        TagType.COPYRIGHT,
        TagType.GENERAL,
        TagType.META,
    ]
    tag = Tag(
        name="".join([random.choice(string.ascii_letters) for _ in range(7)]),
        type=random.choice(tagtypes),
    )
    tag.save_to_db()
    return tag


def random_news(author: User) -> NewsPost:
    news_posts = [
        "Onani acquired by Titter!",
        "Official Onani IRC server!",
        "Fatass don-chan in a Tuxedo, wtf??!",
        "Free sex for free no survey",
    ]
    news = NewsPost(
        title=random.choice(news_posts),
        content="".join([random.choice(string.ascii_letters) for _ in range(2048)]),
        author=author.id,
    )
    news.save_to_db()
    return news


@app.cli.command("init-db")
def init_db():
    try:
        db.create_all(app=app)
    except Exception as e:
        print("Unable to create DB,", e)
    else:
        print("Created DB")


@app.cli.command("drop-db")
def drop_db():
    try:
        db.drop_all(app=app)
    except Exception as e:
        print("Unable to drop DB,", e)
    else:
        print("Dropped DB")
        try:
            db.create_all(app=app)
        except Exception as e:
            print("Unable to create DB,", e)
        else:
            print("Created DB")


@app.cli.command("seed-db")
def seed_db():
    for _ in range(10):
        user = random_user()
        tag1 = random_tag()
        user.tag_blacklist.append(tag1)
        tag2 = random_tag()
        tag1.aliases.append(tag2)
        user.tag_blacklist.append(tag2)
        user.ban = Ban(
            user=user.id,
            reason="Cockhead",
            expires=datetime.utcnow() + timedelta(days=50),
        )
    for _ in range(10):
        random_news(author=User.query.first())
    db.session.commit()
    print("Database has been seeded")


@app.cli.command("create-root")
def create_root():
    root = create_user(
        username="Root",
        password="Root1",
        email="root@onanis.me",
        permissions=UserPermissions.OWNER,
    )

    root.settings.biography = ":don::desuwa:"
    root.settings.avatar = "/static/image/looking.png"
    root.settings.connections = {
        "deviantart": "https://www.deviantart.com/vore",
        "discord": "dirt#3009",
        "github": "https://github.com/Mattlau04",
        "patreon": "https://www.patreon.com/dankpods/posts",
        "pixiv": "https://www.pixiv.net/en/users/19183275",
        "twitter": "https://twitter.com/kapsikkum",
        "paypal": "https://www.paypal.com/paypalme/onani",  # Disclaimer: i do not know this person. do not send them money.
    }

    db.session.commit()


@app.cli.command("add-user")
@click.option("--username")
@click.option("--email")
@click.option("--password")
@click.option("--perms")
def add_user(username, email, password, perms):
    create_user(
        username=username,
        email=email,
        password=password,
        permissions=UserPermissions(int(perms)),
    )
    print("User added to database")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
