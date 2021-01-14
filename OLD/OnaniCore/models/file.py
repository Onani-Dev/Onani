# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-24 20:29:37
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-09 01:05:29


from typing import Union


class File(object):
    """
    Onani File object (For posts and avatars)
    """

    __slots__ = (
        "_directory",
        "_filename",
        "_filesize",
        "_hash",
        "_height",
        "_thumbnail",
        "_width",
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
        self._directory = directory
        self._filename = filename
        self._thumbnail = thumbnail
        self._hash = hash
        self._width = width
        self._height = height
        self._filesize = filesize

    @property
    def directory(self) -> str:
        return self._directory

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def thumbnail(self) -> Union[str, None]:
        return self._thumbnail

    @property
    def full_path(self) -> str:
        return self.directory + self.filename

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def filesize(self) -> int:
        return self._filesize

    def to_dict(self) -> dict:
        return {
            "directory": self.directory,
            "filename": self.filename,
            "thumbnail": self.thumbnail,
            "hash": self.hash,
            "width": self.width,
            "height": self.height,
            "filesize": self.filesize,
        }

    def __repr__(self) -> str:
        return str(self.to_dict())
