# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
from compare_locales.parser import PropertiesParser

from fluent.migrate.util import parse, ftl_pattern_to_json
from fluent.migrate.helpers import EXTERNAL_ARGUMENT
from fluent.migrate.transforms import evaluate, PLURALS, REPLACE_IN_TEXT


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


class TestPlural(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            plural = One;Few;Many
        ''')

        self.transform = PLURALS(
            'test.properties',
            'plural',
            EXTERNAL_ARGUMENT('num')
        )

    def test_plural(self):
        self.plural_categories = ('one', 'few', 'many')
        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('''{ $num ->
                    [one] One
                    [few] Few
                   *[many] Many
                }
            ''')
        )

    def test_plural_too_few_variants(self):
        self.plural_categories = ('one', 'few', 'many', 'other')
        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('''{ $num ->
                    [one] One
                    [few] Few
                    [many] Many
                   *[other] Many
                }
            ''')
        )

    def test_plural_too_many_variants(self):
        self.plural_categories = ('one', 'few')
        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('''{ $num ->
                    [one] One
                   *[few] Few
                }
            ''')
        )


class TestPluralOrder(MockContext):
    plural_categories = ('one', 'other', 'few')

    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            plural = One;Other;Few
        ''')

        self.transform = PLURALS(
            'test.properties',
            'plural',
            EXTERNAL_ARGUMENT('num')
        )

    def test_unordinary_order(self):
        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('''{ $num ->
                    [one] One
                    [few] Few
                   *[other] Other
                }
            ''')
        )


class TestPluralReplace(MockContext):
    plural_categories = ('one', 'few', 'many')

    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            plural = One;Few #1;Many #1
        ''')

    def test_plural_replace(self):
        transform = PLURALS(
            'test.properties',
            'plural',
            EXTERNAL_ARGUMENT('num'),
            lambda text: REPLACE_IN_TEXT(
                text,
                {
                    '#1': EXTERNAL_ARGUMENT('num')
                }
            )
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('''{ $num ->
                    [one] One
                    [few] Few { $num }
                   *[many] Many { $num }
                }
            ''')
        )


class TestNoPlural(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            plural-other = Other
            plural-one-other = One;Other
        ''')

    def test_one_category_one_variant(self):
        self.plural_categories = ('other',)
        transform = PLURALS(
            'test.properties',
            'plural-other',
            EXTERNAL_ARGUMENT('num')
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Other')
        )

    def test_one_category_many_variants(self):
        self.plural_categories = ('other',)
        transform = PLURALS(
            'test.properties',
            'plural-one-other',
            EXTERNAL_ARGUMENT('num')
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('One')
        )

    def test_many_categories_one_variant(self):
        self.plural_categories = ('one', 'other')
        transform = PLURALS(
            'test.properties',
            'plural-other',
            EXTERNAL_ARGUMENT('num')
        )

        self.assertEqual(
            evaluate(self, transform).to_json(),
            ftl_pattern_to_json('Other')
        )


class TestEmpty(MockContext):
    plural_categories = ('one', 'few', 'many')

    def setUp(self):
        self.transform = PLURALS(
            'test.properties',
            'plural',
            EXTERNAL_ARGUMENT('num')
        )

    def test_non_default_empty(self):
        self.strings = parse(PropertiesParser, '''
            plural = ;Few;Many
        ''')

        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('''{ $num ->
                    [few] Few
                   *[many] Many
                }
            ''')
        )

    def test_default_empty(self):
        self.strings = parse(PropertiesParser, '''
            plural = One;Few;
        ''')

        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('''{ $num ->
                    [one] One
                    [few] Few
                   *[many] Few
                }
            ''')
        )

    def test_all_empty(self):
        self.strings = parse(PropertiesParser, '''
            plural = ;
        ''')

        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('{""}')
        )

    def test_no_value(self):
        self.strings = parse(PropertiesParser, '''
            plural =
        ''')

        self.assertEqual(
            evaluate(self, self.transform).to_json(),
            ftl_pattern_to_json('{""}')
        )


if __name__ == '__main__':
    unittest.main()
