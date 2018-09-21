# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
from compare_locales.parser import DTDParser

from fluent.migrate.util import parse, ftl_pattern_to_json
from fluent.migrate.transforms import evaluate, COPY, REPLACE
from fluent.migrate.helpers import MESSAGE_REFERENCE


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_source(self, path, key):
        # Ignore path (test.dtd) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


class TestTrim(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
<!ENTITY foo "Foo">
<!ENTITY empty "">
<!ENTITY multiline-one "Foo  \x20
         Bar
">
<!ENTITY multiline-two "
  Foo  \x20
  Bar
">
        ''')

    def test_copy(self):
        transform = COPY('test.dtd', 'foo', trim=True)

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Foo')
        )

    def test_copy_empty(self):
        transform = COPY('test.dtd', 'empty', trim=True)

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{""}')
        )

    def test_copy_multiline_one(self):
        transform = COPY('test.dtd', 'multiline-one', trim=True)

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Foo\n Bar')
        )

    def test_copy_multiline_two(self):
        transform = COPY('test.dtd', 'multiline-two', trim=True)

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Foo\n Bar')
        )

    def test_replace(self):
        transform = REPLACE(
            'test.dtd',
            'foo',
            {
                'Foo': MESSAGE_REFERENCE('replaced')
            },
            trim=True
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{replaced}')
        )

    def test_replace_multiline_one(self):
        transform = REPLACE(
            'test.dtd',
            'multiline-one',
            {
                'Foo': MESSAGE_REFERENCE('replaced')
            },
            trim=True
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{replaced}\n Bar')
        )

    def test_replace_multiline_two(self):
        transform = REPLACE(
            'test.dtd',
            'multiline-two',
            {
                'Foo': MESSAGE_REFERENCE('replaced')
            },
            trim=True
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{replaced}\n Bar')
        )
