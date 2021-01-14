# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-11 23:58:33

from ..utils import setup_logger

log = setup_logger(__name__)


class Note(object):
    """
    Notes for Posts
    """

    __slots__ = ("_post", "_x", "_y", "_width", "_height", "_content")

    def __init__(
        self,
        post,
        x: int = None,
        y: int = None,
        width: int = None,
        height: int = None,
        content: str = None,
    ):
        self._post = post
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._content = content

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        # TODO
        pass

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        # TODO
        pass

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        # TODO
        pass

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        # TODO
        pass

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        # TODO
        pass

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "content": self.content,
        }
