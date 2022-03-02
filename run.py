# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-03 01:50:03

import random
import string
from datetime import datetime, timedelta

from Onani import db, init_app
from Onani.models import Ban, Tag, User
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
    user = User(
        username="root", email="root@onanis.me", permissions=UserPermissions.OWNER
    )
    user.set_password("root")
    user.save_to_db()

    for x in range(0, 10):
        user = User(
            username="".join([random.choice(string.ascii_letters) for _ in range(32)]),
            email="".join([random.choice(string.ascii_letters) for _ in range(6)])
            + "@onanis.me",
        )
        user.set_password("Cumm1")
        user.save_to_db()

        tag1 = Tag(
            name="".join([random.choice(string.ascii_letters) for _ in range(32)])
        )
        tag1.save_to_db()

        user.tag_blacklist.append(tag1)
        db.session.commit()

        tag2 = Tag(
            name="".join([random.choice(string.ascii_letters) for _ in range(32)])
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
