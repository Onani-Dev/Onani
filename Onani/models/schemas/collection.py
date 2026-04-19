# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:14:09
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:11:26
from marshmallow import fields
from Onani.models import Collection

from . import ma


class CollectionSchema(ma.SQLAlchemyAutoSchema):
    posts = ma.Nested("PostSchema", many=True)
    preview_thumbnails = fields.Method("get_preview_thumbnails", dump_only=True)

    def get_preview_thumbnails(self, obj):
        previews = []
        for post in obj.posts.limit(4).all():
            url = post.thumbnail(size="large")
            if url:
                previews.append({"url": url, "rating": post.rating.value if post.rating else "g"})
        return previews

    class Meta:
        model = Collection
