# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 20:07:09
import random
import string
from datetime import datetime, timedelta

import click

from Onani import db, init_app
from Onani.models import Ban, Tag, User
from Onani.models.news import NewsPost
from Onani.models.tag import TagType
from Onani.models.user import UserPermissions

app = init_app()


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
    news_posts = """Onani acquired by Titter!
Official Onani IRC server!
Fatass don-chan in a Tuxedo, wtf??!
Free sex for free no survey""".splitlines()
    tagtypes = [
        TagType.ARTIST,
        TagType.BANNED,
        TagType.CHARACTER,
        TagType.COPYRIGHT,
        TagType.GENERAL,
        TagType.META,
    ]
    pfps = [
        "/static/image/armagan.gif",
        "/static/image/default.png",
        "/static/image/dirt.gif",
        "/static/image/looking.png",
        "/static/image/sonic_fun.png",
    ]
    root = User(
        username="Root", email="root@onanis.me", permissions=UserPermissions.OWNER
    )
    root.set_password("Root1")
    root.save_to_db()
    root.settings.biography = ":don::desuwa:"
    root.settings.deviantart = "/fun"
    root.settings.discord = "/fun"
    root.settings.github = "/fun"
    root.settings.patreon = "/fun"
    root.settings.pixiv = "/fun"
    root.settings.twitter = "/fun"
    root.settings.avatar = "/static/image/looking.png"

    db.session.commit()

    for _ in range(10):
        news = NewsPost(
            title=f"{random.choice(news_posts)}-{random.randint(0,9999)}",
            content="".join([random.choice(string.ascii_letters) for _ in range(2048)]),
            author=root.id,
        )
        news.save_to_db()

    for _ in range(10):
        user = User(
            username="".join([random.choice(string.ascii_letters) for _ in range(32)]),
            email="".join([random.choice(string.ascii_letters) for _ in range(6)])
            + "@onanis.me",
        )
        user.set_password("Cumm1")
        user.save_to_db()
        user.settings.avatar = random.choice(pfps)
        tag1 = Tag(
            name="".join([random.choice(string.ascii_letters) for _ in range(32)]),
            type=random.choice(tagtypes),
        )
        tag1.save_to_db()

        user.tag_blacklist.append(tag1)
        db.session.commit()

        tag2 = Tag(
            name="".join([random.choice(string.ascii_letters) for _ in range(32)]),
            type=random.choice(tagtypes),
        )
        tag1.aliases.append(tag2)
        tag2.save_to_db()

        user.tag_blacklist.append(tag2)

        db.session.commit()

        ban = Ban(
            user=user.id,
            reason="Cockhead",
            expires=datetime.utcnow() + timedelta(days=50),
        )
        ban.save_to_db()
    print("Database has been seeded")


@app.cli.command("add-user")
@click.option("--username")
@click.option("--email")
@click.option("--password")
@click.option("--perms")
def add_user(username, email, password, perms):
    user = User(username=username, email=email, permissions=UserPermissions(int(perms)))
    user.set_password(password)
    user.save_to_db()
    print("User added to database")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
