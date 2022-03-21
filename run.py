# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-22 01:52:51
import random
import string
from datetime import datetime, timedelta

import click

from Onani import db, init_app
from Onani.controllers import create_user
from Onani.models import Ban, Tag, User, NewsPost, TagType, UserRoles

from datetime import timezone

app = init_app()


def random_user() -> User:
    return create_user(
        username="".join([random.choice(string.ascii_letters) for _ in range(8)]),
        password="Onani1",
    )


def random_tag() -> Tag:
    tagtypes = list(TagType.get_all().values())
    return Tag(
        name="".join([random.choice(string.ascii_letters) for _ in range(7)]),
        type=random.choice(tagtypes),
    )


def random_news(author: User) -> NewsPost:
    news_posts = [
        "Onani acquired by Titter!",
        "Official Onani IRC server!",
        "Fatass don-chan in a Tuxedo, wtf??!",
        "Free sex for free no survey",
    ]
    return NewsPost(
        title=random.choice(news_posts),
        content="".join([random.choice(string.ascii_letters) for _ in range(2048)]),
        author=author.id,
    )


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
    m = []

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
            expires=datetime.now(timezone.utc) + timedelta(days=50),
        )

        m.extend([user, tag1, tag2])

    m.extend(random_news(author=User.query.first()) for _ in range(10))

    db.session.add_all(m)
    db.session.commit()
    print("Database has been seeded")


@app.cli.command("create-root")
def create_root():
    root = create_user(
        username="Root",
        password="Root1",
        email="root@onanis.me",
        role=UserRoles.OWNER,
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
    db.session.add(root)
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
        role=UserRoles(int(perms)),
    )
    print("User added to database")
