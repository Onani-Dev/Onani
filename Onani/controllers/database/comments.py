# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-03 16:59:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-03 21:19:54
from Onani.models import Post, User, PostComment

from . import db


def create_comment(post: Post, author: User, content: str) -> PostComment:
    """Create a comment on a post.

    Args:
        post (Post): The post to add the comment to.
        author (User): The user who is posting the comment.
        content (str): The content of the comment.

    Returns:
        PostComment: The comment database object
    """
    comment = PostComment()
    comment.author = author
    comment.content = content
    comment.post = post

    db.session.add(comment)
    db.session.commit()

    return comment
