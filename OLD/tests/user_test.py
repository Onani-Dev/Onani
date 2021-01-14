# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-18 16:41:43
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-05 19:42:47
import datetime
import random
import string
import unittest

from OnaniCore import *


class TestUser(unittest.TestCase):
    def setUp(self):
        # Start Connection to MongoDB
        self.onaniDB = DatabaseController()

    # def test_creation(self):
    #     # Test if trying to create a user without a password raises an exception
    #     with self.assertRaises(
    #         OnaniDatabaseException,
    #         msg="Creating a user with no password did not raise an exception",
    #     ):
    #         self.onaniDB.add_user()

    #     # Test account creation
    #     user = self.onaniDB.add_user(password="test")

    #     # Test if trying to create a duplicate raises an exception
    #     with self.assertRaises(
    #         OnaniDatabaseException,
    #         msg="Creating a duplicate user did not raise an exception.",
    #     ):
    #         self.onaniDB.add_user(username=user.username, password="test")

    # def test_banning(self):
    #     # Create a user
    #     user = self.onaniDB.add_user(password="test")

    #     # Test Banning and unbanning
    #     user.ban("Automated Test", datetime.timedelta(days=243090))
    #     self.assertEqual(
    #         user.permissions.value,
    #         0,
    #         msg="User did not have the banned permission value",
    #     )
    #     self.assertTrue(user.is_banned, msg="User is_banned was not True.")
    #     user.unban()
    #     self.assertEqual(
    #         user.permissions.value,
    #         1,
    #         msg="User did not have the member permissions value",
    #     )
    #     user.ban("Automated Test", datetime.timedelta(days=243090))

    # def test_settings(self):
    #     # Create a user
    #     user = self.onaniDB.add_user(password="test")

    #     # Check the settings
    #     self.assertEquals(
    #         user.settings.avatar.full_path,
    #         "/image/default.png",
    #         msg="User settings avatar was not set to Default.png.",
    #     )
    #     self.assertEquals(
    #         user.settings.bio,
    #         str(),
    #         msg="User settings bio was not set to empty string.",
    #     )

    #     # Change the settings
    #     user.edit_settings(
    #         bio="User created with an automated test.",
    #         avatar=File("looking.png", "/image/"),
    #     )
    #     self.assertEquals(
    #         user.settings.avatar.full_path,
    #         "/image/looking.png",
    #         msg="User settings avatar was not set to the edited value.",
    #     )
    #     self.assertEquals(
    #         user.settings.bio,
    #         "User created with an automated test.",
    #         msg="User settings bio was not set to the edited value.",
    #     )

    # def test_username_edit(self):
    #     # Create a user
    #     user = self.onaniDB.add_user(password="test")

    #     # Store original
    #     original_username = user.username

    #     # Store new
    #     new_username = "".join(
    #         random.choice(
    #             string.ascii_uppercase + string.ascii_lowercase + string.digits
    #         )
    #         for x in range(10)
    #     )

    #     # change it
    #     user.username = new_username

    #     # test if changed
    #     self.assertNotEqual(
    #         user.username, original_username, msg="Username did not change."
    #     )

    # def test_api_key(self):
    #     # Create a user
    #     user = self.onaniDB.add_user(password="test")

    #     # Store original
    #     original_key = user.api_key

    #     # Regen
    #     user.regen_api_key()

    #     # Test if changed
    #     self.assertNotEqual(user.api_key, original_key, msg="Api key did not change.")

    # def test_authenticate(self):
    #     # Create a user
    #     user = self.onaniDB.add_user(password="test")

    #     self.assertTrue(
    #         user.authenticate("test"), msg="Authentication did not return True."
    #     )


if __name__ == "__main__":
    unittest.main()
