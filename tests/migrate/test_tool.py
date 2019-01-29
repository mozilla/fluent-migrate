# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
import os
import shutil
import tempfile

from fluent.migrate.tool import Migrator
import hglib


class TestSerialize(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.migrator = Migrator(
            'de',
            os.path.join(self.root, 'reference'),
            os.path.join(self.root, 'localization'),
            False
        )

    def tearDown(self):
        self.migrator.close()
        shutil.rmtree(self.root)

    def test_empty(self):
        self.migrator.serialize_changeset({})
        self.assertEqual(os.listdir(self.root), [])

    def test_dry(self):
        self.migrator.dry_run = True
        self.migrator.serialize_changeset({
            'd/f': 'a line of text\n',
        })
        self.assertEqual(os.listdir(self.root), [])

    def test_wet(self):
        self.migrator.serialize_changeset({
            'd1/f1': 'a line of text\n',
            'd2/f2': 'a different line of text\n',
        })
        # Walk our serialized localization dir, but
        # make the directory be relative to our root.
        walked = sorted(
            (os.path.relpath(dir, self.root), dirs, files)
            for dir, dirs, files in os.walk(self.root)
        )
        self.assertEqual(
            walked,
            [
                ('.', ['localization'], []),
                ('localization', ['d1', 'd2'], []),
                ('localization/d1', [], ['f1']),
                ('localization/d2', [], ['f2']),
            ]
        )


class TestCommit(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.migrator = Migrator(
            'de',
            os.path.join(self.root, 'reference'),
            os.path.join(self.root, 'localization'),
            False
        )
        loc_dir = os.path.join(self.migrator.localization_dir, 'd1')
        os.makedirs(loc_dir)
        with open(os.path.join(loc_dir, 'f1'), 'w') as f:
            f.write('first line\n')
        client = hglib.init(self.migrator.localization_dir)
        client.open()
        client.commit(
            message='Initial commit',
            user='Jane',
            addremove=True,
        )
        client.close()

    def tearDown(self):
        self.migrator.close()
        shutil.rmtree(self.root)

    def test_wet(self):
        '''Commit message docstring, part {index}.'''
        with open(
            os.path.join(self.migrator.localization_dir, 'd1', 'f1'), 'a'
        ) as f:
            f.write('second line\n')
        self.migrator.commit_changeset(self.test_wet.__doc__, 'Axel', 2)
        tip = self.migrator.client.tip()
        self.assertEqual(tip.rev, b'1')
        self.assertEqual(tip.author, b'Axel')
        self.assertEqual(tip.desc, b'Commit message docstring, part 2.')
