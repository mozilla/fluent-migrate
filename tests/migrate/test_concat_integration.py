# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
from compare_locales.parser import PropertiesParser, DTDParser

import fluent.syntax.ast as FTL
from fluent.migrate.util import parse, ftl_pattern_to_json
from fluent.migrate.helpers import VARIABLE_REFERENCE, MESSAGE_REFERENCE
from fluent.migrate.transforms import CONCAT, COPY, REPLACE
from fluent.migrate.evaluator import Evaluator


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_legacy_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val

    def evaluate(self, node):
        return self.evaluator.visit(node)


class TestConcatLiteral(MockContext):
    def setUp(self):
        self.evaluator = Evaluator(self)
        self.strings = parse(DTDParser, '''
            <!ENTITY update.failed.start        "Update failed. ">
            <!ENTITY update.failed.linkText     "Download manually">
            <!ENTITY update.failed.end          "!">
        ''')

    def test_concat_literal(self):
        transform = CONCAT(
            COPY('test.properties', 'update.failed.start'),
            FTL.TextElement('<a>'),
            COPY('test.properties', 'update.failed.linkText'),
            FTL.TextElement('</a>'),
            COPY('test.properties', 'update.failed.end'),
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json('Update failed. <a>Download manually</a>!')
        )


class TestConcatInterpolate(MockContext):
    def setUp(self):
        self.evaluator = Evaluator(self)
        self.strings = parse(DTDParser, '''
            <!ENTITY channel.description.start  "You are on the ">
            <!ENTITY channel.description.end    " channel.">
        ''')

    def test_concat_placeable(self):
        transform = CONCAT(
            COPY('test.dtd', 'channel.description.start'),
            FTL.Placeable(VARIABLE_REFERENCE('channelname')),
            COPY('test.dtd', 'channel.description.end'),
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json('You are on the { $channelname } channel.')
        )

    def test_concat_expression(self):
        transform = CONCAT(
            COPY('test.dtd', 'channel.description.start'),
            VARIABLE_REFERENCE('channelname'),
            COPY('test.dtd', 'channel.description.end'),
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json('You are on the { $channelname } channel.')
        )


class TestConcatReplace(MockContext):
    def setUp(self):
        self.evaluator = Evaluator(self)
        self.strings = parse(DTDParser, '''
            <!ENTITY community.start       "&brandShortName; is designed by ">
            <!ENTITY community.mozillaLink "&vendorShortName;">
            <!ENTITY community.middle      ", a ">
            <!ENTITY community.creditsLink "global community">
            <!ENTITY community.end         " working together to…">
        ''')

    def test_concat_replace(self):
        transform = CONCAT(
            REPLACE(
                'test.dtd',
                'community.start',
                {
                    '&brandShortName;': MESSAGE_REFERENCE(
                        'brand-short-name'
                    )
                }
            ),
            FTL.TextElement('<a>'),
            REPLACE(
                'test.properties',
                'community.mozillaLink',
                {
                    '&vendorShortName;': MESSAGE_REFERENCE(
                        'vendor-short-name'
                    )
                }
            ),
            FTL.TextElement('</a>'),
            COPY('test.dtd', 'community.middle'),
            FTL.TextElement('<a>'),
            COPY('test.dtd', 'community.creditsLink'),
            FTL.TextElement('</a>'),
            COPY('test.dtd', 'community.end')
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json(
                '{ brand-short-name } is designed by '
                '<a>{ vendor-short-name }</a>, a <a>global community</a> '
                'working together to…'
            )
        )


if __name__ == '__main__':
    unittest.main()
