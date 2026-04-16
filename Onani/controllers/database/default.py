# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-24 02:10:53
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-24 02:26:44
import json

from Onani.models import Tag

from . import db


def create_default_tags(filename: str = "meta.json") -> list:
    """Create default tags from a json file.

    Args:
        filename (str, optional): The json file's name. Defaults to "meta.json".

    Returns:
        list: List of tag objects that were inserted.
    """
    tags = []

    with open(f"./Onani/defaults/{filename}") as fh:
        data = json.load(fh)

    for d in data:
        tag = Tag.query.filter_by(name=d["name"]).first()
        if not tag:
            tags.append(Tag(**d))

    db.session.add_all(tags)

    db.session.commit()

    return tags
