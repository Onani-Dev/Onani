# -*- coding: utf-8 -*-
import io
import importlib
import importlib.util
import os
import threading
from typing import Iterable

from onani.models import PostRating, Tag, TagType
from onani.models.post import FileType

from .files import shard_path
from .posts import set_tags

_RUNTIME_LOCK = threading.Lock()
_RUNTIME_CACHE: dict[str, object] = {
    "key": None,
    "runtime": None,
}
_VIDEO_FORMATS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}
_SKIP_PREFIXES = ("rating:", "score:")
_RATING_TAG_MAP = {
    "rating:g": PostRating.GENERAL,
    "rating:general": PostRating.GENERAL,
    "rating:safe": PostRating.GENERAL,
    "rating:q": PostRating.QUESTIONABLE,
    "rating:questionable": PostRating.QUESTIONABLE,
    "rating:s": PostRating.SENSITIVE,
    "rating:sensitive": PostRating.SENSITIVE,
    "rating:e": PostRating.EXPLICIT,
    "rating:explicit": PostRating.EXPLICIT,
}


class DeepDanbooruUnavailableError(RuntimeError):
    pass


def _config_key(config) -> tuple:
    return (
        config.get("DEEPDANBOORU_PROJECT_PATH"),
        config.get("DEEPDANBOORU_MODEL_PATH"),
        config.get("DEEPDANBOORU_TAGS_PATH"),
        config.get("DEEPDANBOORU_COMPILE_MODEL"),
        config.get("DEEPDANBOORU_ALLOW_GPU"),
    )


def get_deepdanbooru_status(config) -> dict:
    enabled = bool(config.get("DEEPDANBOORU_ENABLED"))
    project_path = config.get("DEEPDANBOORU_PROJECT_PATH")
    model_path = config.get("DEEPDANBOORU_MODEL_PATH")
    tags_path = config.get("DEEPDANBOORU_TAGS_PATH")

    status = {
        "enabled": enabled,
        "available": False,
        "configured": False,
        "threshold": float(config.get("DEEPDANBOORU_THRESHOLD", 0.5)),
        "max_tags": int(config.get("DEEPDANBOORU_MAX_TAGS", 24)),
        "reason": None,
    }

    if not enabled:
        status["reason"] = "DeepDanbooru is disabled in configuration."
        return status

    if project_path:
        status["configured"] = True
        if not os.path.isdir(project_path):
            status["reason"] = f"Project path does not exist: {project_path}"
            return status
        if not os.path.isfile(os.path.join(project_path, "project.json")):
            status["reason"] = f"project.json is missing from {project_path}"
            return status
        if not os.path.isfile(os.path.join(project_path, "tags.txt")):
            status["reason"] = f"tags.txt is missing from {project_path}"
            return status
    elif model_path or tags_path:
        if not model_path or not tags_path:
            status["reason"] = "Both model_path and tags_path are required when project_path is not set."
            return status
        status["configured"] = True
        if not os.path.isfile(model_path):
            status["reason"] = f"Model path does not exist: {model_path}"
            return status
        if not os.path.isfile(tags_path):
            status["reason"] = f"Tags path does not exist: {tags_path}"
            return status
    else:
        status["reason"] = "Set deepdanbooru.project_path or both model_path and tags_path."
        return status

    if importlib.util.find_spec("deepdanbooru") is None:
        status["reason"] = "Python package 'deepdanbooru' is not installed."
        return status

    if importlib.util.find_spec("tensorflow") is None:
        status["reason"] = "Python package 'tensorflow' is not installed."
        return status

    if importlib.util.find_spec("tensorflow_io") is None:
        status["reason"] = "Python package 'tensorflow-io' is not installed."
        return status

    status["available"] = True
    return status


def _load_runtime(config) -> dict:
    status = get_deepdanbooru_status(config)
    if not status["available"]:
        raise DeepDanbooruUnavailableError(status["reason"] or "DeepDanbooru is unavailable.")

    key = _config_key(config)
    with _RUNTIME_LOCK:
        if _RUNTIME_CACHE["key"] == key and _RUNTIME_CACHE["runtime"] is not None:
            return _RUNTIME_CACHE["runtime"]  # type: ignore[return-value]

        if not config.get("DEEPDANBOORU_ALLOW_GPU"):
            os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

        try:
            dd = importlib.import_module("deepdanbooru")
            tf = importlib.import_module("tensorflow")
        except ModuleNotFoundError as exc:
            raise DeepDanbooruUnavailableError(
                f"Missing Python dependency: {exc.name}"
            ) from exc

        project_path = config.get("DEEPDANBOORU_PROJECT_PATH")
        compile_model = bool(config.get("DEEPDANBOORU_COMPILE_MODEL"))
        if project_path:
            model = dd.project.load_model_from_project(project_path, compile_model=compile_model)
            tags = dd.project.load_tags_from_project(project_path)
        else:
            model = tf.keras.models.load_model(config["DEEPDANBOORU_MODEL_PATH"], compile=compile_model)
            tags = dd.data.load_tags(config["DEEPDANBOORU_TAGS_PATH"])

        runtime = {
            "dd": dd,
            "model": model,
            "tags": tags,
        }
        _RUNTIME_CACHE["key"] = key
        _RUNTIME_CACHE["runtime"] = runtime
        return runtime


def _normalize_tag_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _serialize_suggestions(tag_scores: Iterable[tuple[str, float]]) -> list[dict]:
    cleaned: list[tuple[str, float]] = []
    seen = set()
    for raw_name, score in tag_scores:
        name = _normalize_tag_name(raw_name)
        if not name or name.startswith(_SKIP_PREFIXES) or name in seen:
            continue
        seen.add(name)
        cleaned.append((name, float(score)))

    existing_tags = {
        tag.name: tag
        for tag in Tag.query.filter(Tag.name.in_([name for name, _score in cleaned])).all()
    }

    suggestions = []
    for name, score in cleaned:
        existing = existing_tags.get(name)
        if existing and existing.type == TagType.BANNED:
            continue
        tag_type = existing.type.name.lower() if existing and existing.type else "general"
        raw_tag = f"{tag_type}:{name}" if tag_type != "general" else name
        suggestions.append({
            "name": name,
            "tag": raw_tag,
            "type": tag_type,
            "score": round(score, 4),
            "exists": existing is not None,
        })
    return suggestions


def _infer_rating(tag_scores: Iterable[tuple[str, float]]) -> tuple[PostRating | None, float | None]:
    best_rating = None
    best_score = None
    for raw_name, score in tag_scores:
        normalized = _normalize_tag_name(raw_name)
        mapped = _RATING_TAG_MAP.get(normalized)
        if mapped is None:
            continue
        if best_score is None or score > best_score:
            best_rating = mapped
            best_score = float(score)
    return best_rating, best_score


def suggest_labels_for_bytes(
    image_bytes: bytes,
    config,
    threshold: float | None = None,
    max_tags: int | None = None,
) -> dict:
    runtime = _load_runtime(config)
    threshold = float(config.get("DEEPDANBOORU_THRESHOLD", 0.5) if threshold is None else threshold)
    max_tags = int(config.get("DEEPDANBOORU_MAX_TAGS", 24) if max_tags is None else max_tags)

    image_input = io.BytesIO(image_bytes)
    tag_scores = list(runtime["dd"].commands.evaluate_image(image_input, runtime["model"], runtime["tags"], 0.0))
    tag_scores.sort(key=lambda item: item[1], reverse=True)

    rating, rating_score = _infer_rating(tag_scores)
    visible_scores = [item for item in tag_scores if item[1] >= threshold]

    return {
        "tags": _serialize_suggestions(visible_scores[:max_tags]),
        "rating": rating.value if rating is not None else None,
        "rating_score": round(rating_score, 4) if rating_score is not None else None,
    }


def suggest_tags_for_bytes(image_bytes: bytes, config, threshold: float | None = None, max_tags: int | None = None) -> list[dict]:
    return suggest_labels_for_bytes(
        image_bytes,
        config,
        threshold=threshold,
        max_tags=max_tags,
    )["tags"]


def _post_image_input(post, images_dir: str) -> str:
    ext = (post.file_type or "").lower()
    if ext in _VIDEO_FORMATS or getattr(post, "type", None) == FileType.VIDEO:
        stem = post.filename.rsplit(".", 1)[0]
        thumb_path = shard_path(images_dir, f"{stem}.jpg")
        if not os.path.isfile(thumb_path):
            raise ValueError(f"Post #{post.id} does not have a generated video thumbnail.")
        return thumb_path

    file_path = shard_path(images_dir, post.filename)
    if not os.path.isfile(file_path):
        raise ValueError(f"Post #{post.id} media file is missing from disk.")
    return file_path


def suggest_tags_for_post(post, config, threshold: float | None = None, max_tags: int | None = None) -> list[dict]:
    image_path = _post_image_input(post, config["IMAGES_DIR"])
    with open(image_path, "rb") as handle:
        return suggest_tags_for_bytes(handle.read(), config, threshold=threshold, max_tags=max_tags)


def suggest_labels_for_post(post, config, threshold: float | None = None, max_tags: int | None = None) -> dict:
    image_path = _post_image_input(post, config["IMAGES_DIR"])
    with open(image_path, "rb") as handle:
        return suggest_labels_for_bytes(handle.read(), config, threshold=threshold, max_tags=max_tags)


def _tag_to_raw(tag) -> str:
    tag_type = getattr(tag.type, "name", "GENERAL").lower()
    return f"{tag_type}:{tag.name}" if tag_type != "general" else tag.name


def apply_suggested_tags_to_post(post, suggested_tags: Iterable[str], tag_char_limit: int, post_min_tags: int) -> int:
    current_tags = {_tag_to_raw(tag) for tag in post.tags}
    additions = {tag for tag in suggested_tags if tag and tag not in current_tags}
    if not additions:
        return 0

    desired_tags = current_tags | additions
    set_tags(
        post,
        desired_tags,
        current_tags,
        can_create_tags=True,
        tag_char_limit=tag_char_limit,
        post_min_tags=post_min_tags,
    )
    return len(additions)