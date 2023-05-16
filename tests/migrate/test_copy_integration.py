import unittest
from datetime import datetime
import os
import shutil
import tempfile
import hglib

from fluent.migrate.helpers import transforms_from
from fluent.migrate import tool


class MockMigrationModule:
    __name__ = 'tests.migrate.some'
    @staticmethod
    def migrate(ctx):
        '''No bug - test conversions, part {index}.'''
        ctx.add_transforms(
            'd1/f1.ftl',
            'd1/f1.ftl',
            transforms_from('''\
target = { COPY("d1/f1.dtd", "one.with") }
''')
        )


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'ref', 'd1'))
        with open(os.path.join(self.root, 'ref', 'd1', 'f1.ftl'), 'w') as f:
            f.write('''\
one = old entry
    .with = an attribute needs to stay for now.
target = should be migrated.
''')
        self.timestamps = [1272837600, 1335996000]
        os.makedirs(os.path.join(self.root, 'pl', 'd1'))
        with open(os.path.join(self.root, 'pl', 'd1', 'f1.ftl'), 'w') as f:
            f.write('one = first line\n')
        with open(os.path.join(self.root, 'pl', 'd1', 'f1.dtd'), 'w') as f:
            f.write('<!ENTITY one "first line">\n')
        self.client = client = hglib.init(
            os.path.join(self.root, 'pl'),
            encoding='utf-8'
        )
        client.open()
        client.commit(
            message='Initial commit',
            user='Hüsker Dü'.encode(),
            date=datetime.fromtimestamp(self.timestamps[0]),
            addremove=True,
        )
        with open(os.path.join(self.root, 'pl', 'd1', 'f1.ftl'), 'a') as f:
            f.write('    .with = attribute\n')
        with open(os.path.join(self.root, 'pl', 'd1', 'f1.dtd'), 'a') as f:
            f.write('<!ENTITY one.with "attribute">\n')
        client.commit(
            message='Second commit',
            user='😂'.encode(),
            date=datetime.fromtimestamp(self.timestamps[1]),
            addremove=True,
        )

    def tearDown(self):
        self.client.close()
        shutil.rmtree(self.root)

    def test_transform(self):
        tool.main(
            'pl',
            os.path.join(self.root, 'ref'),
            os.path.join(self.root, 'pl'),
            [MockMigrationModule()],
            False,
        )
        tip = self.client.tip()
        # There is only one commit
        self.assertEqual(tip.rev, b'2')
        self.assertEqual(tip.author, '😂'.encode())
        with open(os.path.join(self.root, 'pl', 'd1', 'f1.ftl')) as f:
            content = f.read()
        self.assertEqual(
            content,
            """\
one = first line
    .with = attribute
target = attribute
"""
        )
