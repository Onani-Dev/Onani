# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-24 20:29:37
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-07 21:34:30


class File(object):
    """
    Onani File object (For posts and avatars)
    """

    __slots__ = (
        "directory",
        "filename",
        "filesize",
        "full_path",
        "hash",
        "height",
        "thumbnail",
        "width",
    )

    def __init__(
        self,
        filename: str = "default.png",
        directory: str = "/image/",
        thumbnail: str = None,
        hash: str = "22230440e7724ceb91804c4fd9e29a53",
        width: int = 800,
        height: int = 800,
        filesize: int = 19476,
    ) -> None:
        self.directory = directory
        self.filename = filename
        self.thumbnail = thumbnail
        self.full_path = directory + filename
        self.hash = hash
        self.width = width
        self.height = height
        self.filesize = filesize

    def to_dict(self) -> dict:
        return {x: getattr(self, x) for x in self.__slots__ if x != "full_path"}

    def __repr__(self) -> str:
        return str(self.to_dict())
