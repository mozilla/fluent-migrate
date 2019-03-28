# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest

from fluent.migrate.transforms import (
    chain_elements,
    Transform,
)
from fluent.migrate.util import ftl_pattern_to_json
from fluent.syntax import ast as FTL


class TestChainElements(unittest.TestCase):
    def test_expression(self):
        self.assertEqual(
            FTL.Pattern(
                elements=[
                    FTL.Placeable(
                        expression=FTL.NumberLiteral(4)
                    )
                ]
            ).to_json(),
            FTL.Pattern(
                elements=list(chain_elements([
                    FTL.NumberLiteral(4)
                ]))
            ).to_json()
        )

    def test_flatten(self):
        """Test that chain_elements flattens Patterns into their
        elements.
        This only works one level deep.
        """
        elements = list(chain_elements([
            FTL.TextElement("some"),
            FTL.Pattern(
                elements=[
                    FTL.TextElement("other"),
                ]
            ),
            FTL.TextElement("text"),
        ]))
        self.assertEqual(
            FTL.Pattern(
                elements=elements
            ).to_json(),
            FTL.Pattern(
                elements=[
                    FTL.TextElement("some"),
                    FTL.TextElement("other"),
                    FTL.TextElement("text"),
                ]
            ).to_json()
        )


class TestPatternOf(unittest.TestCase):
    maxDiff = None

    def test_empty(self):
        pattern = Transform.pattern_of()
        self.assertEqual(
            pattern.to_json(),
            ftl_pattern_to_json('{""}')
        )

    def test_leading_white(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("  word")
        )
        self.assertEqual(
            pattern.to_json(),
            ftl_pattern_to_json('{"  "}word')
        )

    def test_trailing_white(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("word  ")
        )
        self.assertEqual(
            pattern.to_json(),
            ftl_pattern_to_json('word{"  "}')
        )

    def test_adjoin(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("word"),
            FTL.TextElement(" "),
            FTL.TextElement("of"),
            FTL.StringLiteral(" "),
            FTL.TextElement("mouth")
        )
        self.assertEqual(
            pattern.to_json(),
            ftl_pattern_to_json('word of mouth')
        )

    def test_inner_literal(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("apples"),
            FTL.StringLiteral("\\u002B"),
            FTL.TextElement("oranges")
        )
        self.assertEqual(
            pattern.to_json(),
            ftl_pattern_to_json('apples{ "\\u002B" }oranges')
        )
