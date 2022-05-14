# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 07:36:56
import click

from Onani import db, init_app
from Onani.controllers import create_default_tags, create_user
from Onani.models import UserRoles

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


@app.cli.command("add-user")
@click.option("--username")
@click.option("--email")
@click.option("--password")
@click.option("--role")
def add_user(username, email, password, role: UserRoles = UserRoles.MEMBER):
    create_user(
        username=username,
        email=email,
        password=password,
        role=UserRoles(int(role)),
    )
    print("User added to database")


@app.cli.command("tags")
@click.option("--filename")
def default_tags(filename):
    tags = create_default_tags(filename=filename)
    print(f"Added {len(tags)} tags from {filename} to database")
