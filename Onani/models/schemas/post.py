# -*- coding: utf-8 -*-
from marshmallow import fields
from Onani.models import Post

from . import ma


class PostTagSchema(ma.Schema):
    name = fields.Str()
    type = fields.Str()


class PostSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Post
        include_fk = True

    tags = fields.Method("get_tags", dump_only=True)
    title = fields.Str(dump_only=True)
    score = fields.Int(dump_only=True)
    file_url = fields.Str(dump_only=True)
    water_count = fields.Int(dump_only=True)
    thumbnail_url = fields.Method("get_thumbnail_url", dump_only=True)

    def get_tags(self, obj):
        return [{"id": t.id, "name": t.name, "type": t.type.name.lower()} for t in obj.tags]

    def get_thumbnail_url(self, obj):
        return obj.thumbnail(size="large")
