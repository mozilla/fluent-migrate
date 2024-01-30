import unittest
from datetime import datetime
from os import makedirs
from os.path import join
import shutil
from subprocess import run
import tempfile
import hglib

from fluent.migrate.blame import Blame
from fluent.migrate.repo_client import RepoClient


class MockedBlame(Blame):
    def __init__(self, unicode_content):
        super().__init__(None)
        self.content = unicode_content

    def readFile(self, parser, path):
        parser.readUnicode(self.content)


class TestBlame(unittest.TestCase):
    def test_handle_file(self):
        blame = MockedBlame(
            """\
jane = first
joe = second
"""
        )
        blame.handleFile(
            "file.properties",
            [
                ("Jane Doe <jane@example.tld>", 10000),
                ("Joe Doe <joe@example.tld>", 11000),
            ],
        )
        self.assertEqual(
            blame.users,
            [
                "Jane Doe <jane@example.tld>",
                "Joe Doe <joe@example.tld>",
            ],
        )
        self.assertEqual(
            blame.blame,
            {"file.properties": {"jane": (0, 10000), "joe": (1, 11000)}},
        )

    def test_fluent(self):
        blame = MockedBlame(
            """\
jane = first
    .joe = second
"""
        )
        blame.handleFile(
            "file.ftl",
            [
                ("Jane Doe <jane@example.tld>", 10000),
                ("Joe Doe <joe@example.tld>", 11000),
            ],
        )
        self.assertEqual(
            blame.users,
            [
                "Jane Doe <jane@example.tld>",
                "Joe Doe <joe@example.tld>",
            ],
        )
        self.assertEqual(
            blame.blame, {"file.ftl": {"jane": (0, 10000), "jane.joe": (1, 11000)}}
        )


class TestHgIntegration(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.timestamps = (1272837600, 1335996000)
        makedirs(join(self.root, "d1"))
        with open(join(self.root, "d1", "f1.ftl"), "w") as f:
            f.write("one = first line\n")
        self.hgclient = hgclient = hglib.init(self.root, encoding="utf-8")
        hgclient.open()
        hgclient.commit(
            message="Initial commit",
            user="Hüsker Dü".encode(),
            date=datetime.fromtimestamp(self.timestamps[0]),
            addremove=True,
        )
        with open(join(self.root, "d1", "f1.ftl"), "a") as f:
            f.write("two = second line\n")
        hgclient.commit(
            message="Second commit",
            user="😂".encode(),
            date=datetime.fromtimestamp(self.timestamps[1]),
            addremove=True,
        )

    def tearDown(self):
        self.hgclient.close()
        shutil.rmtree(self.root)

    def test_attribution(self):
        client = RepoClient(self.root)
        blame = Blame(client)
        rv = blame.attribution(["d1/f1.ftl"])
        client.close()
        self.assertEqual(
            rv,
            {
                "authors": ["Hüsker Dü", "😂"],
                "blame": {
                    "d1/f1.ftl": {
                        "one": (0, self.timestamps[0]),
                        "two": (1, self.timestamps[1]),
                    }
                },
            },
        )


class TestGitIntegration(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.timestamps = (1272837600, 1335996000)

        proc = run(
            ["git", "init"], capture_output=True, cwd=self.root, encoding="utf-8"
        )
        if proc.returncode != 0:
            raise Exception(proc.stderr or "git init failed")
        client = RepoClient(self.root)

        makedirs(join(self.root, "d1"))
        with open(join(self.root, "d1", "f1.ftl"), "w") as f:
            f.write("one = first line\n")
        client._git("add", ".")
        client._git(
            "commit",
            f"--date={datetime.fromtimestamp(self.timestamps[0])}",
            "--author=Hüsker Dü <husker@example.com>",
            "--message=Initial commit",
        )

        with open(join(self.root, "d1", "f1.ftl"), "a") as f:
            f.write("two = second line\n")
        client._git(
            "commit",
            "--all",
            f"--date={datetime.fromtimestamp(self.timestamps[1])}",
            "--author=😂 <foo@bar.baz>",
            "--message=Second commit",
        )

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_attribution(self):
        client = RepoClient(self.root)
        self.assertIsNone(client.hgclient)
        blame = Blame(client)
        rv = blame.attribution(["d1/f1.ftl"])
        self.assertEqual(
            rv,
            {
                "authors": ["Hüsker Dü <husker@example.com>", "😂 <foo@bar.baz>"],
                "blame": {
                    "d1/f1.ftl": {
                        "one": (0, self.timestamps[0]),
                        "two": (1, self.timestamps[1]),
                    }
                },
            },
        )
