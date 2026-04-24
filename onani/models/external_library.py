# -*- coding: utf-8 -*-
import datetime

from . import db


class ExternalLibrary(db.Model):
    """A directory on the server filesystem configured for periodic scanning.

    Analogous to Immich's external libraries. The Celery task
    ``scan_library`` walks the path, discovers media files, and imports any
    new ones as posts.
    """

    __tablename__ = "external_libraries"

    id: int = db.Column(db.Integer, primary_key=True)

    name: str = db.Column(db.String(200), nullable=False)

    # Absolute path to the directory on the host / container.
    path: str = db.Column(db.String, nullable=False)

    enabled: bool = db.Column(
        db.Boolean, nullable=False, default=True, server_default="true"
    )

    recursive: bool = db.Column(
        db.Boolean, nullable=False, default=True, server_default="true"
    )

    # Default explicitness rating applied to imported posts if not otherwise
    # determined.  One of "g" / "q" / "e" (PostRating values).
    default_rating: str = db.Column(
        db.String(1), nullable=False, default="q", server_default="q"
    )

    # Space-separated tag string pre-applied to every imported post.
    default_tags: str = db.Column(db.Text, nullable=True)

    owner_id: int = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    last_scan_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    # IDLE / SCANNING / SUCCESS / FAILED
    last_scan_status: str = db.Column(db.String(20), nullable=True)

    # Celery task ID of the currently-running (or last) scan so the client
    # can poll progress the same way it polls import jobs.
    last_scan_task_id: str = db.Column(db.String(36), nullable=True)

    owner = db.relationship(
        "User",
        backref=db.backref("external_libraries", lazy="dynamic"),
    )

    files = db.relationship(
        "ExternalLibraryFile",
        back_populates="library",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def file_count(self) -> int:
        return self.files.count()

    @property
    def imported_count(self) -> int:
        return self.files.filter_by(status="IMPORTED").count()

    def __repr__(self):
        return f"<ExternalLibrary {self.id} {self.name!r} path={self.path!r}>"


class ExternalLibraryFile(db.Model):
    """Tracks a single media file discovered inside an ExternalLibrary.

    Statuses:
    - PENDING   — found in scan, not yet imported.
    - IMPORTED  — successfully imported as a post.
    - FAILED    — import was attempted but raised an error (see ``error``).
    - MISSING   — was present in a previous scan but absent in the latest.
    """

    __tablename__ = "external_library_files"

    id: int = db.Column(db.Integer, primary_key=True)

    library_id: int = db.Column(
        db.Integer,
        db.ForeignKey("external_libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Path as recorded at first discovery — may be absolute or relative to
    # library.path.  We store the absolute path for unambiguous lookups.
    file_path: str = db.Column(db.Text, nullable=False)

    sha256_hash: str = db.Column(db.String(64), nullable=True, index=True)

    # PENDING / IMPORTED / FAILED / MISSING
    status: str = db.Column(
        db.String(20), nullable=False, default="PENDING", server_default="PENDING"
    )

    # FK to the post created for this file (null until IMPORTED).
    post_id: int = db.Column(
        db.Integer,
        db.ForeignKey("posts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Human-readable error message for FAILED entries.
    error: str = db.Column(db.Text, nullable=True)

    first_seen_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    last_seen_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    imported_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    library = db.relationship("ExternalLibrary", back_populates="files")

    post = db.relationship(
        "Post",
        backref=db.backref("library_file", uselist=False),
    )

    __table_args__ = (
        db.UniqueConstraint("library_id", "file_path", name="uq_library_file_path"),
    )

    def __repr__(self):
        return (
            f"<ExternalLibraryFile {self.id} status={self.status!r}"
            f" path={self.file_path!r}>"
        )
