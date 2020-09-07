# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-25 22:29:02
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-07 06:08:45
import datetime
import random
import string
import unittest

from OnaniCore import *


class TestTag(unittest.TestCase):
    def setUp(self):
        # Start Connection to MongoDB
        self.onaniDB = DatabaseController("mongodb://localhost:27017/")

    def test_creation(self):
        # Test tag creation
        tag = self.onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )

        # Try to add tag again
        with self.assertRaises(
            ValueError,
            msg="Tag did not raise exception when created again with same name",
        ):
            self.onaniDB.add_tag(tag.string)

    def test_aliases(self):
        # Create tag
        tag = self.onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )

        # Create an alias name
        alias = self.onaniDB._parse_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            )
        )

        # add to aliases
        tag.add_alias(alias)
        self.assertIn(alias, tag.aliases, msg="Alias was not in the tag aliases.")

        # Try to add again
        tag.add_alias(alias)

        self.assertEqual(
            len(tag.aliases), 1, msg="Len of aliases was more than expected (> 1)"
        )

        # Test removing alias
        remove = tag.aliases[0]
        tag.remove_alias(remove)
        self.assertNotIn(
            remove, tag.aliases, msg="Alias was not removed from the alias list."
        )

    def test_banning(self):
        # Create tag
        tag = self.onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )

        # Ban it
        tag.ban()
        self.assertEqual(tag.type.value, 0, msg="Tag did not have the banned value.")

        # Unban it
        tag.unban()
        self.assertEquals(
            tag.type.value,
            TagType.GENERAL.value,
            msg="Tag did not have the General tag value.",
        )

    def test_discovery(self):
        # Create tag
        tag = self.onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )
        alias = self.onaniDB._parse_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            )
        )
        tag.add_alias(alias)

        # Discover the tags
        test1 = self.onaniDB.get_tag(alias)
        test2 = self.onaniDB.get_tag(tag.string)
        self.assertIsNotNone(test1)
        self.assertEquals(test1.aliases[0], alias)
        self.assertIsNotNone(test2)
        self.assertEquals(test2.string, tag.string)

    def test_modification(self):
        # Create tag
        tag = self.onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )

        # Add and check if it added
        tag.edit_description("This is a modification test")
        self.assertEquals(
            tag.description,
            "This is a modification test",
            msg="Tag description did not equal the modified tag.",
        )

        new_name = "This is a modification test " + "".join(
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for x in range(10)
        )
        tag.edit_name(new_name)
        self.assertEquals(
            tag.string,
            self.onaniDB._parse_tag(new_name),
            msg="Tag did not change name.",
        )

        # Test type changing
        tag.edit_type(TagType.CHARACTER)
        self.assertEquals(
            tag.type.value,
            TagType.CHARACTER.value,
            msg="Tag did not change to the Character value.",
        )

    def test_post_count_increase(self):
        # Create tag
        tag = self.onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )

        # increase count by 2
        tag.modify_post_count(2)

        # Check if really 2
        self.assertEqual(tag.post_count, 2, msg="Post count was not 2.")

        # decrease count by 1
        tag.modify_post_count(-1)

        # Check if 1
        self.assertEqual(tag.post_count, 1, msg="Post count was not 1.")

    def test_popularity_increase(self):
        # Create tag
        tag = self.onaniDB.add_tag(
            "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for x in range(10)
            ),
            description="Automated Test",
        )

        # increase count by 0.2
        tag.modify_popularity(0.2)

        # Check if really 0.2
        self.assertEqual(tag.popularity, 0.2, msg="Popularity was not 0.2.")

        # decrease count by 0.1
        tag.modify_popularity(-0.1)

        # Check if 0.1
        self.assertEqual(tag.popularity, 0.1, msg="Popularity was not 1.")


if __name__ == "__main__":
    unittest.main()
