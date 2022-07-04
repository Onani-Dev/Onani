# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-16 02:07:20
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-04 16:33:13

from __future__ import annotations

import datetime
import html
import os
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Union

from Onani.controllers.utils import is_url, natural_join
from Onani.models.user._user import User
from sqlalchemy import func
from sqlalchemy.orm import validates
from sqlalchemy.orm.query import Query
from sqlalchemy_utils import ChoiceType, JSONType

from ..tag import Tag, TagType
from . import FileType, PostRating, PostStatus, db

if TYPE_CHECKING:
    from Onani.models.post.note import Note

post_upvotes = db.Table(
    "post_upvotes",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
)

post_downvotes = db.Table(
    "post_downvotes",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
)

post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id")),
)


class Post(db.Model):
    """
    Post object model
    """

    __tablename__ = "posts"

    # The post primary key
    id: int = db.Column(db.Integer, primary_key=True)

    # The time the post was created.
    uploaded_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    # The status of the post. if it is deleted for any reason it will become PostStatus.DELETED
    status: PostStatus = db.Column(
        ChoiceType(PostStatus, impl=db.Integer()),
        default=PostStatus.PENDING,
        nullable=False,
    )

    # The explicitness rating of a post. will be manually set by uploader and can be changed by an admin or moderator.
    rating: PostRating = db.Column(
        ChoiceType(PostRating, impl=db.String(length=1)),
        default=PostRating.QUESTIONABLE,
        nullable=False,
    )

    # The post's source. will be a url.
    source: str = db.Column(db.String)

    # the post's description
    description: str = db.Column(db.String)

    # The post's uploader. is a user.
    uploader_id: int = db.Column(db.Integer, db.ForeignKey("users.id"))
    uploader: User = db.relationship(
        "User", backref="uploads", lazy="joined", uselist=False
    )

    # The post's tags. will be a list of tags that can be appended to.
    tags: List[Tag] = db.relationship(
        "Tag", secondary=post_tags, backref="posts", lazy="dynamic"
    )

    # Post's upvoters. users. contributes to the post's rating/score
    upvoters: Query = db.relationship(
        "User", secondary=post_upvotes, backref="post_upvoters", lazy="dynamic"
    )

    # Post's downvoters. users. contributes to the post's rating/score (reddit moment)
    downvoters: Query = db.relationship(
        "User", secondary=post_downvotes, backref="post_downvoters", lazy="dynamic"
    )

    # The post's comments. will be filtered for naughty words or other bad things.
    comments: Query = db.relationship(
        "PostComment", backref="comments", lazy="dynamic", viewonly=True
    )

    # Will be the link to the original post that it is imported from. will be none if the post is not imported
    imported_from: Union[str, None] = db.Column(db.String)

    # The file's notes. those little thingys on the image over the japanese text :)
    notes: List[Note] = db.relationship("Note", backref="file_notes", lazy="joined")

    # ===== File =====
    filename: str = db.Column(db.String, unique=True)
    original_filename: str = db.Column(db.String)
    file_type: str = db.Column(db.String)

    sha256_hash: str = db.Column(db.String, unique=True, index=True)
    md5_hash: str = db.Column(db.String, index=True)

    width: int = db.Column(db.Integer)
    height: int = db.Column(db.Integer)

    filesize: int = db.Column(db.Integer)

    type: FileType = db.Column(
        ChoiceType(FileType, impl=db.Integer()),
        default=FileType.IMAGE,
        nullable=False,
    )

    @validates("description")
    def validate_description(self, key, description):
        return html.escape(description)

    @validates("source")
    def validate_source(self, key, source):
        return html.escape(source)

    @property
    def source_hostname(self) -> Union[str, None]:
        """Return the hostname for the post's source

        Returns:
            Union[str, None]: The sources Hostname, or None if there is no source
        """
        return (
            self.source.split("/")[2]
            if self.source and is_url(self.source)
            else self.source or None
        )

    @property
    def score(self) -> int:
        """Get the rating score of this post.

        Returns:
            int: The Score.
        """
        return (
            self.upvoters.with_entities(func.count()).scalar()
            - self.downvoters.with_entities(func.count()).scalar()
        )

    @property
    def is_imported(self) -> bool:
        """Check if this post is imported or not.

        Returns:
            bool: Imported post yes or no :)
        """
        return bool(self.imported_from)

    @property
    def sorted_tags(self) -> Dict[TagType, List[Tag]]:
        # Dictionary we are going to add the types as keys to lists for the tags
        sorted_tags = defaultdict(list)

        # Get all tags in self
        for tag in sorted(self.tags, key=lambda t: t.type.name.capitalize()):
            # append the tag to the type list
            sorted_tags[tag.type].append(tag)

        # Return the sorted dict
        return {x: sorted(sorted_tags[x], key=lambda t: t.name) for x in sorted_tags}

    @property
    def title(self) -> str:
        """Makes a nice title describing the post. This should never be an empty string."""
        sorted_tags = self.sorted_tags
        characters = sorted_tags.get(TagType.CHARACTER, None)
        artists = sorted_tags.get(TagType.ARTIST, None)
        copyrights = sorted_tags.get(TagType.COPYRIGHT, None)

        # First we get all 3 strings
        # TODO: pick char based on popularity and not alphabetically
        if characters is not None:
            char_str = natural_join(
                [c.humanized.capitalize() for c in characters], max_length=5
            )
        else:
            char_str = ""

        if artists is not None:
            artist_str = f"drawn by {natural_join([a.humanized.capitalize() for a in artists], max_length=3)}"

        else:
            artist_str = ""

        if copyrights is not None:
            copyright_str = natural_join(
                [a.humanized.capitalize() for a in copyrights], max_length=1
            )
        else:
            copyright_str = ""

        title = ""
        if char_str:
            # If we have chars, copyrights will be in parenthesis
            title += char_str
            if copyright_str:
                title += f" ({copyright_str})"
        else:
            # If we don't have chars, copyrights won't be in parenthesis
            # Also this will work even is there's no copyright
            title += copyright_str

        if artist_str:
            # We need to lstrip in case title was still empty
            title = f"{title} {artist_str}".lstrip()

        if not title:  # We never want an empty title
            title = f"#{self.id}"

        return title

    @property
    def tag_string(self) -> str:
        """A string with all the post's tag"""
        return " ".join(t.name for t in self.tags)

    # ===== File =====

    @validates("sha256_hash")
    def validate_hash(self, key, hash_):
        if hash_:
            if Post.query.filter(Post.sha256_hash == hash_).first():
                raise ValueError("Post already exists.")
            return hash_
        return None

    @validates("original_filename")
    def validate_origfilename(self, key, filename):
        return html.escape(filename)

    @validates("imported_from")
    def validate_imported_from(self, key, url):
        return html.escape(url)

    def thumbnail(self, size: str = "small") -> str:
        return f"/images/thumbnail/{self.filename}?size={size}"

    @property
    def sample(self) -> str:
        return f"/sample/{self.filename}"

    @property
    def file_url(self) -> str:
        return f"/images/{self.filename}"

    def delete(self):
        """Delete this file from the database and the disk.

        Raises:
            Exception: The file couldn't be deleted.
        """
        os.remove(self.file_url)
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"<Post {self.__dict__}>"
