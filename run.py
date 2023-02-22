# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   Mattlau04
# @Last Modified time: 2023-02-22 20:42:16
import click
import string
import random

from Onani import db, init_app
from Onani.controllers import create_default_tags
from Onani.models import UserPermissions, UserRoles, User

app = init_app()


@app.cli.command("init-db")
def init_db():
    """Creates the database."""
    try:
        db.create_all(app=app)
    except Exception as e:
        print("Unable to create DB,", e)
    else:
        print("Created DB")


@app.cli.command("drop-db")
def drop_db():
    """Drops all table from the database."""
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
    """Adds tags from a file to the database."""
    tags = create_default_tags(filename=filename)
    print(f"Added {len(tags)} tags from {filename} to database")


@app.cli.command("add-owner")
@click.option("--id")
def add_owner(id):
    """Makes a user into a owner."""
    user = User.query.filter(User.id == id).first()
    if user is None:
        raise ValueError("User not found.")

    user.permissions = UserPermissions.ADMINISTRATION
    user.role = UserRoles.OWNER
    db.session.commit()

    print(f"Made {user.username} an owner.")


@app.cli.command("reset-password")
@click.option("--id")
def reset_password(id):
    """Changes a user's password to a new random one."""
    user = User.query.filter(User.id == id).first()
    if user is None:
        raise ValueError("User not found.")

    new_password = "".join(random.choices(string.ascii_letters, k=8))
    user.set_password(new_password)
    db.session.commit()

    print(f"Reset {user.username}'s password.")
    print(f"New password: {new_password}")


@app.cli.command("disable-otp")
@click.option("--id")
def reset_password(id):
    """Disable OTP auth for a user."""
    user = User.query.filter(User.id == id).first()
    if user is None:
        raise ValueError("User not found.")

    user.otp_enabled = False
    db.session.commit()

    print(f"Disabled OTP for {user.username}.")
