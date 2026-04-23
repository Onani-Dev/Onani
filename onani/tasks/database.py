# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-29 02:27:38
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-30 16:38:52

from typing import Optional
from celery import shared_task

from . import db


@shared_task
def database_test(user_id: int) -> Optional[str]:
    from onani.models import User, UserSchema

    return UserSchema().dump(User.query.filter_by(id=user_id).first())


@shared_task
def delete_user_posts(user_id: int) -> dict:
    from onani.models import Post, User

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return {"deleted": 0, "error": "User not found"}

    posts = user.posts.all()
    count = 0
    for post in posts:
        try:
            post.delete()
            count += 1
        except Exception:
            db.session.rollback()

    return {"deleted": count}
