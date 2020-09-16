# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 14:21:03
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-14 03:17:12

import functools

import emoji
from flask_login import current_user
from flask_socketio import disconnect, emit, join_room, leave_room, send

from OnaniCore import html_escape, custom_emoji

from .. import socketio
from . import main


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)

    return wrapped


@socketio.on("message", namespace="/chat")
@authenticated_only
def handle_message(message):
    message["text"] = message["text"].strip()
    if len(message["text"]) > 400:
        emit("notification", {"data": "Your message was too long. (> 400)"})
    elif len(message["text"]) < 1:
        pass
    else:
        emit(
            "message",
            {
                "user": current_user.username,
                "user_id": current_user.id,
                "message": emoji.emojize(
                    html_escape(message["text"]), use_aliases=True,
                ),
            },
            room=message["room"],
        )


@socketio.on("join", namespace="/chat")
@authenticated_only
def on_join(data):
    room = data["room"]
    join_room(room)
    if room == "general":
        return  # Save spamming general
    emit(
        "connection",
        {"data": f"{current_user.username} has joined {html_escape(room)}."},
        room=room,
    )


@socketio.on("leave", namespace="/chat")
@authenticated_only
def on_leave(data):
    room = data["room"]
    leave_room(room)
    if room == "general":
        return  # Save spamming general
    emit(
        "disconnection",
        {"data": f"{current_user.username} has left {html_escape(room)}."},
        broadcast=True,
        room=room,
    )
