# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-08 08:47:25
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-08 08:58:08


from onani.models import NewsType, User, NewsPost

from . import db


def create_news(title: str, content: str, type: NewsType, author: User):
    # Create the article
    article = NewsPost()

    # Set post data
    article.author = author
    article.title = title
    article.content = content
    article.type = type

    # add to database and commit
    db.session.add(article)
    db.session.commit()

    # return :) hehe
    return article
