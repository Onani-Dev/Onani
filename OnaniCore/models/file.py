# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-24 20:29:37
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-25 00:53:28


class File(object):
    """
    Onani File object (For posts and avatars)
    """

    __slots__ = ("filename", "directory", "full_path", "hash", "width", "height")

    def __init__(
        self,
        filename: str = None,
        directory: str = None,
        hash: str = None,
        width: int = None,
        height: int = None,
    ) -> None:
        self.directory = directory
        self.filename = filename
        self.full_path = directory + filename
        self.hash = hash
        self.width = width
        self.height = height

    def to_dict(self) -> dict:
        return {x: getattr(self, x) for x in self.__slots__}

    def __repr__(self) -> str:
        return str(self.to_dict())
