# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
from compare_locales.parser import PropertiesParser

from fluent.migrate.util import parse, ftl_pattern_to_json
from fluent.migrate.transforms import evaluate, COPY


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


class TestCopy(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            foo = Foo
            empty =
            unicode.all = \\u0020
            unicode.begin1 = \\u0020Foo
            unicode.begin2 = \\u0020\\u0020Foo
            unicode.end1 = Foo\\u0020
            unicode.end2 = Foo\\u0020\\u0020
        ''')

    def test_copy(self):
        transform = COPY('test.properties', 'foo')

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Foo')
        )

    def test_copy_empty(self):
        transform = COPY('test.properties', 'empty')

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{""}')
        )

    def test_copy_escape_unicode_all(self):
        transform = COPY('test.properties', 'unicode.all')

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{" "}')
        )

    def test_copy_escape_unicode_begin(self):
        transform = COPY('test.properties', 'unicode.begin1')

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{" "}Foo')
        )

    def test_copy_escape_unicode_begin_many(self):
        transform = COPY('test.properties', 'unicode.begin2')

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{"  "}Foo')
        )

    def test_copy_escape_unicode_end(self):
        transform = COPY('test.properties', 'unicode.end1')

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Foo{" "}')
        )

    def test_copy_escape_unicode_end_many(self):
        transform = COPY('test.properties', 'unicode.end2')

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Foo{"  "}')
        )


if __name__ == '__main__':
    unittest.main()
