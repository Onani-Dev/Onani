# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-18 16:41:43
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-18 19:27:41
import datetime
import unittest

from OnaniCore import *


class TestOnaniDatabase(unittest.TestCase):
    def test_user_creation(self):
        # Test Connection
        onaniDB = DatabaseController("mongodb://localhost:27017/")

        # Test if trying to create a user without a password raises an exception
        with self.assertRaises(ValueError):
            onaniDB.add_user()

        # Test account creation
        user = onaniDB.add_user(password="test")

        # Test if trying to create a duplicate raises an exception
        with self.assertRaises(ValueError):
            onaniDB.add_user(username=user.username, password="test")

        # Test Banning
        user.ban("Automated Test", datetime.timedelta(days=243090))
        self.assertTrue(user.permissions.value == 0)

        # Test if objects are what they are meant to be
        self.assertTrue(isinstance(user, User))
        self.assertTrue(isinstance(user.permissions, UserPermissions))


if __name__ == "__main__":
    unittest.main()
