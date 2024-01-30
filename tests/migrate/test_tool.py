import unittest
import os
from os.path import join, relpath
import shutil
from subprocess import run
import tempfile

from fluent.migrate.repo_client import RepoClient
from fluent.migrate.tool import Migrator
import hglib


class TestSerialize(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.migrator = Migrator(
            "de",
            join(self.root, "reference"),
            join(self.root, "localization"),
            False,
        )

    def tearDown(self):
        self.migrator.close()
        shutil.rmtree(self.root)

    def test_empty(self):
        self.migrator.serialize_changeset({})
        self.assertEqual(os.listdir(self.root), [])

    def test_dry(self):
        self.migrator.dry_run = True
        self.migrator.serialize_changeset(
            {
                "d/f": "a line of text\n",
            }
        )
        self.assertEqual(os.listdir(self.root), [])

    def test_wet(self):
        self.migrator.serialize_changeset(
            {
                "d1/f1": "a line of text\n",
                "d2/f2": "a different line of text\n",
            }
        )
        # Walk our serialized localization dir, but
        # make the directory be relative to our root.
        walked = sorted(
            (relpath(dir, self.root), sorted(dirs), sorted(files))
            for dir, dirs, files in os.walk(self.root)
        )
        self.assertEqual(
            walked,
            [
                (".", ["localization"], []),
                ("localization", ["d1", "d2"], []),
                ("localization/d1", [], ["f1"]),
                ("localization/d2", [], ["f2"]),
            ],
        )


class TestHgCommit(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.migrator = Migrator(
            "de",
            join(self.root, "reference"),
            join(self.root, "localization"),
            False,
        )
        loc_dir = join(self.migrator.localization_dir, "d1")
        os.makedirs(loc_dir)
        with open(join(loc_dir, "f1"), "w") as f:
            f.write("first line\n")
        client = hglib.init(self.migrator.localization_dir)
        client.open()
        client.commit(
            message="Initial commit",
            user="Jane",
            addremove=True,
        )
        client.close()

    def tearDown(self):
        self.migrator.close()
        shutil.rmtree(self.root)

    def test_wet(self):
        """Hg commit message docstring, part {index}."""
        with open(join(self.migrator.localization_dir, "d1", "f1"), "a") as f:
            f.write("second line\n")
        self.migrator.commit_changeset(self.test_wet.__doc__, "Axel", 2)
        tip = self.migrator.client.hgclient.tip()
        self.assertEqual(tip.rev, b"1")
        self.assertEqual(tip.author, b"Axel")
        self.assertEqual(tip.desc, b"Hg commit message docstring, part 2.")


class TestGitCommit(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.migrator = Migrator(
            "de",
            join(self.root, "reference"),
            join(self.root, "localization"),
            False,
        )

        loc_dir = join(self.migrator.localization_dir, "d1")
        os.makedirs(loc_dir)
        with open(join(loc_dir, "f1"), "w") as f:
            f.write("first line\n")

        proc = run(
            ["git", "init"],
            capture_output=True,
            cwd=self.migrator.localization_dir,
            encoding="utf-8",
        )
        if proc.returncode != 0:
            raise Exception(proc.stderr or "git init failed")
        client = RepoClient(self.migrator.localization_dir)
        client._git("add", ".")
        client._git(
            "commit", "--author=Jane <jane@example.com>", "--message=Initial commit"
        )

    def tearDown(self):
        self.migrator.close()
        shutil.rmtree(self.root)

    def test_wet(self):
        """Git commit message docstring, part {index}."""
        with open(join(self.migrator.localization_dir, "d1", "f1"), "a") as f:
            f.write("second line\n")
        self.migrator.commit_changeset(
            self.test_wet.__doc__, "Axel <axel@example.com>", 2
        )
        stdout = self.migrator.client._git(
            "show", "--no-patch", "--pretty=format:%an:%s"
        )
        self.assertEqual(stdout, "Axel:Git commit message docstring, part 2.")
