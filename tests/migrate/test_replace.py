# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
from compare_locales.parser import PropertiesParser

import fluent.syntax.ast as FTL
from fluent.migrate.util import parse, ftl_pattern_to_json
from fluent.migrate.helpers import VARIABLE_REFERENCE
from fluent.migrate.transforms import evaluate, REPLACE


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


class TestReplace(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            empty =
            hello = Hello, #1!
            welcome = Welcome, #1, to #2!
            first = #1 Bar
            last = Foo #1
        ''')

    def test_replace_empty(self):
        transform = REPLACE(
            'test.properties',
            'empty',
            {
                '#1': VARIABLE_REFERENCE('arg')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{""}')
        )

    def test_replace_one(self):
        transform = REPLACE(
            'test.properties',
            'hello',
            {
                '#1': VARIABLE_REFERENCE('username')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Hello, { $username }!')
        )

    def test_replace_two(self):
        transform = REPLACE(
            'test.properties',
            'welcome',
            {
                '#1': VARIABLE_REFERENCE('username'),
                '#2': VARIABLE_REFERENCE('appname')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Welcome, { $username }, to { $appname }!')
        )

    def test_replace_too_many(self):
        transform = REPLACE(
            'test.properties',
            'welcome',
            {
                '#1': VARIABLE_REFERENCE('username'),
                '#2': VARIABLE_REFERENCE('appname'),
                '#3': VARIABLE_REFERENCE('extraname')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Welcome, { $username }, to { $appname }!')
        )

    def test_replace_too_few(self):
        transform = REPLACE(
            'test.properties',
            'welcome',
            {
                '#1': VARIABLE_REFERENCE('username')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Welcome, { $username }, to #2!')
        )

    def test_replace_first(self):
        transform = REPLACE(
            'test.properties',
            'first',
            {
                '#1': VARIABLE_REFERENCE('foo')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('{ $foo } Bar')
        )

    def test_replace_last(self):
        transform = REPLACE(
            'test.properties',
            'last',
            {
                '#1': VARIABLE_REFERENCE('bar')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Foo { $bar }')
        )

    def test_replace_with_placeable(self):
        transform = REPLACE(
            'test.properties',
            'hello',
            {
                '#1': FTL.Placeable(
                    VARIABLE_REFERENCE('user')
                )
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Hello, { $user }!')
        )

    def test_replace_with_text_element(self):
        transform = REPLACE(
            'test.properties',
            'hello',
            {
                '#1': FTL.TextElement('you')
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Hello, you!')
        )

    def test_replace_with_pattern(self):
        transform = REPLACE(
            'test.properties',
            'hello',
            {
                '#1': FTL.Pattern(
                    elements=[
                        FTL.TextElement('<img> '),
                        FTL.Placeable(
                            VARIABLE_REFERENCE('user')
                        )
                    ]
                )
            }
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Hello, <img> { $user }!')
        )


if __name__ == '__main__':
    unittest.main()
