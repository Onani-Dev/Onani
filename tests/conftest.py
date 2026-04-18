# -*- coding: utf-8 -*-
"""
Pytest configuration and shared fixtures for the Onani test suite.
Uses an in-memory SQLite database so no external services are needed.
"""
import os
import tempfile

import pytest

# Set all env vars BEFORE importing the app so config.py picks them up correctly.
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("DB_PASSWORD", "test")
# Use SQLite in-memory so no Postgres is needed during tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Disable Redis for rate limiting in tests
os.environ["RATELIMIT_ENABLED"] = "False"
os.environ["RATELIMIT_STORAGE_URI"] = "memory://"


@pytest.fixture(scope="session")
def app():
    """Create an application instance configured for testing."""
    from Onani import db as _db, init_app

    application = init_app()
    application.config.update(
        TESTING=True,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Disable CSRF for tests
        WTF_CSRF_ENABLED=False,
        # Disable rate limiting for tests
        RATELIMIT_ENABLED=False,
        # Temporary dirs for files
        IMAGES_DIR=tempfile.mkdtemp(),
        AVATARS_DIR=tempfile.mkdtemp(),
        # Celery: run tasks synchronously in tests
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        # Session cookies don't need secure flag in tests
        SESSION_COOKIE_SECURE=False,
        SECRET_KEY="test-secret-key-do-not-use-in-prod",
    )

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database session per test with automatic rollback."""
    from Onani import db as _db

    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        _db.session.bind = connection

        yield _db

        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(app):
    """A test client for the Flask app."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """A test CLI runner for the Flask app."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def _clear_login_state(app):
    """Clear Flask-Login's g._login_user between tests.

    Flask-Login stores the current user in g, which is scoped to the app
    context. With a session-scoped app fixture the same app context is reused
    across all tests, so calling login_user() in one test would bleed into the
    next. Clearing the key here ensures each test starts unauthenticated.
    """
    yield
    from flask import g
    g.pop("_login_user", None)

# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------

@pytest.fixture
def make_user(db, app):
    """Factory fixture to create User instances."""
    from Onani.models import User, UserRoles, UserPermissions, UserSettings

    created = []

    def _make(
        username="testuser",
        password="testpassword",
        email=None,
        role=UserRoles.MEMBER,
        permissions=UserPermissions.DEFAULT,
    ):
        # Ensure unique username in case multiple calls happen
        existing = User.query.filter_by(username=username).first()
        if existing:
            return existing
        user = User(username=username, email=email, role=role, permissions=permissions)
        user.set_password(password)
        if not user.settings:
            user.settings = UserSettings()
        db.session.add(user)
        db.session.commit()
        created.append(user.id)
        return user

    yield _make


@pytest.fixture
def make_tag(db, app):
    """Factory fixture to create Tag instances."""
    from Onani.models import Tag
    from Onani.models.tag.type import TagType

    def _make(name="test_tag", tag_type=TagType.GENERAL):
        existing = Tag.query.filter_by(name=name).first()
        if existing:
            return existing
        tag = Tag(name=name, type=tag_type)
        db.session.add(tag)
        db.session.commit()
        return tag

    yield _make


@pytest.fixture
def make_post(db, app, make_user, make_tag):
    """Factory fixture to create Post instances (without actual files)."""
    from Onani.models import Post
    from Onani.models.post.rating import PostRating
    from Onani.models.post.status import PostStatus

    _post_counter = [0]

    def _make(
        uploader=None,
        filename=None,
        sha256_hash=None,
        md5_hash=None,
        width=800,
        height=600,
        filesize=100000,
        file_type="png",
        rating=PostRating.GENERAL,
        status=PostStatus.APPROVED,
        source="https://example.com",
        tags=None,
    ):
        _post_counter[0] += 1
        n = _post_counter[0]
        if sha256_hash is None:
            sha256_hash = f"sha256hash{n:08d}"
        if md5_hash is None:
            md5_hash = f"md5hash{n:08d}"
        if filename is None:
            filename = f"{sha256_hash}.png"
        if uploader is None:
            uploader = make_user()
        post = Post(
            uploader=uploader,
            filename=filename,
            sha256_hash=sha256_hash,
            md5_hash=md5_hash,
            width=width,
            height=height,
            filesize=filesize,
            file_type=file_type,
            rating=rating,
            status=status,
            source=source,
            original_filename="original.png",
        )
        if tags:
            for tag in tags:
                post.tags.append(tag)
        db.session.add(post)
        db.session.commit()
        return post

    yield _make


@pytest.fixture
def logged_in_client(client, make_user, app):
    """A test client with a logged-in regular user."""
    user = make_user(username="loggedinuser", password="testpassword")
    with client.session_transaction() as sess:
        sess["_user_id"] = user.login_id
        sess["_fresh"] = True
    return client, user


@pytest.fixture
def admin_client(client, make_user, app):
    """A test client with a logged-in admin user."""
    from Onani.models import UserRoles, UserPermissions
    user = make_user(
        username="adminuser",
        password="adminpassword",
        role=UserRoles.ADMIN,
        permissions=UserPermissions.ADMINISTRATION,
    )
    with client.session_transaction() as sess:
        sess["_user_id"] = user.login_id
        sess["_fresh"] = True
    return client, user
