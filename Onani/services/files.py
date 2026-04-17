# -*- coding: utf-8 -*-
import contextlib
import hashlib
import io
import os
import sys
import tempfile
from base64 import b64decode
from typing import Tuple

import ffmpeg
import imagehash
from Onani.models import User
from PIL import Image

from Onani import db


_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}

# Magic-byte signatures → (format_hint, description)
# Checked in order; first match wins.
_VIDEO_MAGIC = [
    (b"\x1a\x45\xdf\xa3", "webm"),        # WebM / MKV
    (b"RIFF",              "avi"),          # AVI (RIFF container)
    (b"\x00\x00\x00\x14ftypqt",  "mov"),  # QuickTime .mov
    (b"\x00\x00\x00",     "mp4"),          # MP4 / MOV (length-prefixed ftyp box)
]


def detect_video_format(data: bytes) -> str | None:
    """Return a format string (e.g. 'mp4') if *data* looks like a video,
    or None if it appears to be a still image or unknown format."""
    if len(data) < 12:
        return None
    # WebM / MKV
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    # AVI
    if data[:4] == b"RIFF" and data[8:12] == b"AVI ":
        return "avi"
    # MP4 / MOV — 'ftyp' box appears at byte offset 4
    if data[4:8] == b"ftyp":
        return "mp4"
    return None


def is_video_url(url: str) -> bool:
    """Return True if the URL path ends with a known video extension."""
    path = url.split("?")[0]  # strip query string
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return ext in _VIDEO_EXTENSIONS


def video_to_gif(video_data: bytes, input_format: str = "mp4", timeout: int = 120) -> bytes:
    """Convert raw video bytes to an animated GIF using ffmpeg.

    Output is capped at 480 px wide, 10 fps. Raises RuntimeError on failure
    or if the conversion exceeds *timeout* seconds.
    """
    fd_in, tmp_in = tempfile.mkstemp(suffix=f".{input_format}")
    fd_out, tmp_out = tempfile.mkstemp(suffix=".gif")
    os.close(fd_in)
    os.close(fd_out)
    try:
        with open(tmp_in, "wb") as f:
            f.write(video_data)

        try:
            proc = (
                ffmpeg
                .input(tmp_in, fflags='+genpts')
                .output(
                    tmp_out,
                    format="gif",
                    vf="fps=10,scale=640:-1:flags=lanczos",
                )
                .overwrite_output()
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            _, stderr_bytes = proc.communicate(timeout=timeout)
            if proc.returncode != 0:
                stderr = stderr_bytes.decode(errors="replace") if stderr_bytes else "(no stderr)"
                raise RuntimeError(f"ffmpeg conversion failed: {stderr.strip()}")
        except Exception as exc:
            # Kill the subprocess if it's still alive (e.g. on timeout)
            with contextlib.suppress(Exception):
                proc.kill()
            if isinstance(exc, RuntimeError):
                raise
            stderr_msg = getattr(exc, 'stderr', b'')
            if isinstance(stderr_msg, bytes):
                stderr_msg = stderr_msg.decode(errors="replace")
            raise RuntimeError(f"ffmpeg error: {stderr_msg or exc}") from exc

        with open(tmp_out, "rb") as f:
            return f.read()
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_in)
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_out)


def determine_meta_tags(
    width: int,
    height: int,
    filesize: int,
    file_type: str,
    min_tags: int,
    tag_count: int | None = None,
) -> list[str]:
    """Return a list of meta tag names to apply based on image dimensions/size.

    Args:
        min_tags: Minimum required tag count (from config).
        tag_count: Current tag count; if below min_tags adds meta:tag_request.
    """
    meta_tags = []

    if width >= 5400 and height <= 512 or width <= 512 and height >= 5400:
        meta_tags.append("meta:long")
    elif width >= 10000 and height >= 10000:
        meta_tags.append("meta:extremely_high_resolution")
    elif width >= 3200 and height >= 2400:
        meta_tags.append("meta:very_high_resolution")
    elif width >= 1600 and height >= 1200:
        meta_tags.append("meta:high_resolution")
    elif width <= 500 and height <= 500:
        meta_tags.append("meta:low_resolution")

    if filesize >= 15728640:
        meta_tags.append("meta:extremely_large_filesize")
    elif filesize >= 5242880:
        meta_tags.append("meta:large_filesize")

    if file_type == "gif":
        meta_tags.append("meta:animated")

    if tag_count is not None and tag_count < min_tags:
        meta_tags.append("meta:tag_request")

    return meta_tags


def get_video_data(
    video_data: bytes,
    input_format: str,
) -> Tuple[io.BytesIO, int, str, str, int, int, str, str, None]:
    """Like get_file_data but for raw video bytes.

    Uses ffprobe to extract width/height. Returns the same 9-tuple as
    get_file_data so callers need no special handling.  The perceptual hash
    (phash) position is always ``None`` for video files.
    """
    import json as _json

    video_file = io.BytesIO(video_data)
    filesize = sys.getsizeof(video_data)
    hash_md5 = hashlib.md5(video_file.getbuffer()).hexdigest()
    hash_sha256 = hashlib.sha256(video_file.getbuffer()).hexdigest()

    # Use ffprobe to get dimensions
    width, height = 0, 0
    fd, tmp = tempfile.mkstemp(suffix=f".{input_format}")
    os.close(fd)
    try:
        with open(tmp, "wb") as f:
            f.write(video_data)
        try:
            proc = (
                ffmpeg.probe(tmp)
            )
            for stream in proc.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = stream.get("width", 0)
                    height = stream.get("height", 0)
                    break
        except Exception:
            pass
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)

    # Normalise to mp4/webm — keep the detected format as the extension
    file_type = input_format if input_format in ("mp4", "webm", "mov", "avi", "mkv") else "mp4"
    filename = f"{hash_sha256}.{file_type}"

    video_file.seek(0)
    return (video_file, filesize, hash_sha256, hash_md5, width, height, filename, file_type, None)


def create_video_thumbnail(video_path: str, thumbnail_path: str, seek_seconds: int = 1) -> bool:
    """Extract a single JPEG frame from *video_path* and write it to *thumbnail_path*.

    Returns True on success, False if ffmpeg fails (e.g. very short clip).
    """
    fd, tmp = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    try:
        proc = (
            ffmpeg
            .input(video_path, ss=seek_seconds)
            .output(tmp, vframes=1, format="image2", vcodec="mjpeg")
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        _, _ = proc.communicate(timeout=30)
        if proc.returncode != 0 or os.path.getsize(tmp) == 0:
            # Fallback: grab frame at t=0
            proc2 = (
                ffmpeg
                .input(video_path, ss=0)
                .output(tmp, vframes=1, format="image2", vcodec="mjpeg")
                .overwrite_output()
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            proc2.communicate(timeout=30)
            if proc2.returncode != 0:
                return False
        import shutil
        shutil.move(tmp, thumbnail_path)
        return True
    except Exception:
        return False
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)


def get_file_data(
    file_data: bytes,
) -> Tuple[io.BytesIO, int, str, str, int, int, str, str, str]:
    """Parse raw file bytes, compute hashes and image dimensions.

    Returns:
        (image_file, filesize, sha256, md5, width, height, filename, file_type, phash)

        The *phash* element is the hex string of a perceptual hash (pHash)
        computed by ImageHash.  It can be used to detect near-duplicate images
        that are visually identical but differ in metadata or compression.
    """
    image_file = io.BytesIO(file_data)
    filesize = sys.getsizeof(file_data)
    hash_md5 = hashlib.md5(image_file.getbuffer()).hexdigest()
    hash_sha256 = hashlib.sha256(image_file.getbuffer()).hexdigest()

    im = Image.open(image_file)
    width, height = im.size
    file_type = im.format.lower()

    hash_phash = str(imagehash.phash(im))

    filename = f"{hash_sha256}.{file_type}"

    return (
        image_file,
        filesize,
        hash_sha256,
        hash_md5,
        width,
        height,
        filename,
        file_type,
        hash_phash,
    )


def create_avatar(user: User, base64_file: str, avatars_dir: str) -> str:
    """Decode a base64 image, save it as the user's avatar, and return the URL.

    Args:
        user: The user whose avatar to update.
        base64_file: A data-URL string (e.g. ``data:image/png;base64,...``).
        avatars_dir: Filesystem path where avatars are stored (from config).

    Raises:
        ValueError: If the image is not square.
    """
    avatar = b64decode(base64_file.split(",")[1])

    os.makedirs(avatars_dir, exist_ok=True)

    im = Image.open(io.BytesIO(avatar))
    # Center-crop to square
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side))
    # Resize to a sensible avatar size
    im = im.resize((256, 256), Image.LANCZOS)

    buf = io.BytesIO()
    fmt = im.format or "PNG"
    im.save(buf, format=fmt)
    buf.seek(0)
    processed = buf.read()

    hash_sha256 = hashlib.sha256(processed).hexdigest()
    ext = fmt.lower().replace("jpeg", "jpg")
    filename = f"{hash_sha256}.{ext}"

    url = f"/avatars/{filename}"
    filepath = os.path.join(avatars_dir, filename)

    with open(filepath, "wb") as f:
        f.write(processed)

    if user.settings.avatar:
        old_path = os.path.join(avatars_dir, os.path.basename(user.settings.avatar))
        with contextlib.suppress(FileNotFoundError):
            os.remove(old_path)

    user.settings.avatar = url
    db.session.commit()

    return url
