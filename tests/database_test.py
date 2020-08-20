# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-18 16:41:43
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-20 13:57:05
import datetime
import random
import string
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

    def test_tag_creation(self):
        # Test Connection
        onaniDB = DatabaseController("mongodb://localhost:27017/")

        # Test tag creation
        tag = onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )

        # Try to add tag again
        with self.assertRaises(ValueError):
            onaniDB.add_tag(tag.string)

        # Test aliases
        alias = onaniDB._parse_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            )
        )
        tag.add_alias(alias)
        self.assertIn(alias, tag.aliases)

        # Try to add again
        tag.add_alias(alias)

        # Test banning
        tag.ban()
        self.assertEqual(tag.type.value, 0)

        # Test discovery
        test1 = onaniDB.get_tag(alias)
        test2 = onaniDB.get_tag(tag.string)
        self.assertIsNotNone(test1)
        self.assertEquals(test1.aliases[0], alias)
        self.assertIsNotNone(test2)
        self.assertEquals(test2.string, tag.string)

        # Test modification
        test1.edit_description("This is a modification test")
        self.assertEquals(test1.description, "This is a modification test")
        new_name = "This is a modification test " + "".join(
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for x in range(10)
        )
        test1.edit_name(new_name)
        self.assertEquals(test1.string, onaniDB._parse_tag(new_name))

        # Test removing alias
        remove = test1.aliases[0]
        test1.remove_alias(remove)
        self.assertNotIn(remove, test1.aliases)

        # Test unbanning
        test1.unban()
        self.assertEquals(test1.type.value, TagType.GENERAL.value)

        # Test type changing
        test1.edit_type(TagType.CHARACTER)
        self.assertEquals(test1.type.value, TagType.CHARACTER.value)


if __name__ == "__main__":
    unittest.main()
