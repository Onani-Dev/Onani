# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-31 14:50:54
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-08-31 14:56:10
import unittest

from OnaniCore import *


class TestPost(unittest.TestCase):
    def setUp(self):
        # Start Connection to MongoDB
        self.onaniDB = DatabaseController("mongodb://localhost:27017/")

    def test_creation(self):
        post = self.onaniDB.add_post(
            PostFile(None, None, None), [], PostData(self.onaniDB)
        )
        self.assertIsInstance(post, Post, msg="Creation did not return a post object.")


if __name__ == "__main__":
    unittest.main()
