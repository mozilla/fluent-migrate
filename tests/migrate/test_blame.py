# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest

from fluent.migrate.blame import Blame


class MockedBlame(Blame):
    def __init__(self, unicode_content):
        super(MockedBlame, self).__init__(None)
        self.content = unicode_content

    def readFile(self, parser, path):
        parser.readUnicode(self.content)


class TestBlame(unittest.TestCase):
    def test_handle_file(self):
        blame = MockedBlame('''\
jane = first
joe = second
''')
        blame.handleFile({
            "abspath": "file.properties",
            "path": "file.properties",
            "lines": [
                {
                    "date": [10000.0, 0],
                    "user": "Jane Doe <jane@example.tld>",
                    "line": "jane = first\n"
                },
                {
                    "date": [11000.0, 0],
                    "user": "Joe Doe <joe@example.tld>",
                    "line": "joe = second\n"
                }
            ]
        })
        self.assertEqual(
            blame.users,
            [
                "Jane Doe <jane@example.tld>",
                "Joe Doe <joe@example.tld>",
            ]
        )
        self.assertEqual(
            blame.blame,
            {
                "file.properties": {
                    "jane": [0, 10000.0],
                    "joe": [1, 11000.0]
                }
            }
        )
