# -*- coding: utf-8 -*-
from Onani.models import NewsPost, NewsType, User

from Onani import db


def create_news(title: str, content: str, type: NewsType, author: User) -> NewsPost:
    """Create and persist a news article."""
    article = NewsPost()
    article.author = author
    article.title = title
    article.content = content
    article.type = type

    db.session.add(article)
    db.session.commit()

    return article
