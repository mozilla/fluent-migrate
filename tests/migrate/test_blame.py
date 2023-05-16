import unittest
from datetime import datetime
import os
import shutil
import tempfile
import hglib

from fluent.migrate.blame import Blame


class MockedBlame(Blame):
    def __init__(self, unicode_content):
        super().__init__(None)
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

    def test_fluent(self):
        blame = MockedBlame('''\
jane = first
    .joe = second
''')
        blame.handleFile({
            "abspath": "file.ftl",
            "path": "file.ftl",
            "lines": [
                {
                    "date": [10000.0, 0],
                    "user": "Jane Doe <jane@example.tld>",
                    "line": "jane = first\n"
                },
                {
                    "date": [11000.0, 0],
                    "user": "Joe Doe <joe@example.tld>",
                    "line": "    .joe = second\n"
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
                "file.ftl": {
                    "jane": [0, 10000.0],
                    "jane.joe": [1, 11000.0]
                }
            }
        )


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.timestamps = [1272837600, 1335996000]
        os.makedirs(os.path.join(self.root, 'd1'))
        with open(os.path.join(self.root, 'd1', 'f1.ftl'), 'w') as f:
            f.write('one = first line\n')
        self.client = client = hglib.init(self.root, encoding='utf-8')
        client.open()
        client.commit(
            message='Initial commit',
            user='Hüsker Dü'.encode(),
            date=datetime.fromtimestamp(self.timestamps[0]),
            addremove=True,
        )
        with open(os.path.join(self.root, 'd1', 'f1.ftl'), 'a') as f:
            f.write('two = second line\n')
        client.commit(
            message='Second commit',
            user='😂'.encode(),
            date=datetime.fromtimestamp(self.timestamps[1]),
            addremove=True,
        )

    def tearDown(self):
        self.client.close()
        shutil.rmtree(self.root)

    def test_attribution(self):
        blame = Blame(self.client)
        rv = blame.attribution(['d1/f1.ftl'])
        self.assertEqual(
            rv,
            {
                'authors': ['Hüsker Dü', '😂'],
                'blame': {
                    'd1/f1.ftl': {
                        'one': [0, self.timestamps[0]],
                        'two': [1, self.timestamps[1]],
                    }
                }
            }
        )
