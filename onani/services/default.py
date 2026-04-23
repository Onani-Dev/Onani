# -*- coding: utf-8 -*-
import json

from onani.models import Tag

from onani import db


def create_default_tags(filename: str = "meta.json") -> list:
    """Seed the database with default tags read from a JSON defaults file."""
    tags = []

    with open(f"./onani/defaults/{filename}") as fh:
        data = json.load(fh)

    for d in data:
        tag = Tag.query.filter_by(name=d["name"]).first()
        if not tag:
            tags.append(Tag(**d))

    db.session.add_all(tags)
    db.session.commit()

    return tags
