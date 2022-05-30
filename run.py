# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-30 17:00:05
import click

from Onani import db, init_app
from Onani.controllers import create_default_tags
from Onani.models import UserPermissions, UserRoles, User

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
    if app.testing:
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
    else:
        print("Do not do this in production.")


@app.cli.command("tags")
@click.option("--filename")
def default_tags(filename):
    tags = create_default_tags(filename=filename)
    print(f"Added {len(tags)} tags from {filename} to database")


@app.cli.command("add-owner")
@click.option("--id")
def add_owner(id):
    user = User.query.filter(User.id == id).first()
    if user is None:
        raise ValueError("User not found.")

    user.permissions = UserPermissions.ADMINISTRATION
    user.role = UserRoles.OWNER
    db.session.commit()

    print(f"Made {user.username} an owner.")
