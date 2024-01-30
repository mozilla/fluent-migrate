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
                elements=[FTL.Placeable(expression=FTL.NumberLiteral(4))]
            ).to_json(),
            FTL.Pattern(
                elements=list(chain_elements([FTL.NumberLiteral(4)]))
            ).to_json(),
        )

    def test_flatten(self):
        """Test that chain_elements flattens Patterns into their
        elements.
        This only works one level deep.
        """
        elements = list(
            chain_elements(
                [
                    FTL.TextElement("some"),
                    FTL.Pattern(
                        elements=[
                            FTL.TextElement("other"),
                        ]
                    ),
                    FTL.TextElement("text"),
                ]
            )
        )
        self.assertEqual(
            FTL.Pattern(elements=elements).to_json(),
            FTL.Pattern(
                elements=[
                    FTL.TextElement("some"),
                    FTL.TextElement("other"),
                    FTL.TextElement("text"),
                ]
            ).to_json(),
        )


class TestPatternOf(unittest.TestCase):
    maxDiff = None

    def test_empty(self):
        pattern = Transform.pattern_of()
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json('{""}'))

    def test_empty_text(self):
        pattern = Transform.pattern_of(FTL.TextElement(""))
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json('{""}'))

    def test_leading_white(self):
        pattern = Transform.pattern_of(FTL.TextElement("  word"))
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json('{"  "}word'))

    def test_trailing_white(self):
        pattern = Transform.pattern_of(FTL.TextElement("word  "))
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json('word{"  "}'))

    def test_leading_trailing(self):
        pattern = Transform.pattern_of(
            FTL.TextElement(" foo "), FTL.TextElement(" bar ")
        )
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json('{" "}foo  bar{" "}'))

    def test_adjoin(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("word"),
            FTL.TextElement(" "),
            FTL.TextElement("of"),
            FTL.StringLiteral(" "),
            FTL.TextElement("mouth"),
        )
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json("word of mouth"))

    def test_inner_literal(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("apples"),
            FTL.StringLiteral("\\u002B"),
            FTL.TextElement("oranges"),
        )
        self.assertEqual(
            pattern.to_json(), ftl_pattern_to_json('apples{ "\\u002B" }oranges')
        )

    def test_multiline_inside(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("foo\nbar\n\nbaz"),
        )
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json("foo\n bar\n\n baz"))

    def test_multiline_outside(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("\nfoo\nbar\n\n"),
        )
        self.assertEqual(
            pattern.to_json(), ftl_pattern_to_json('{""}\n foo\n bar\n\n {""}')
        )

    def test_multiline_outside_explicit(self):
        pattern = Transform.pattern_of(
            FTL.TextElement(" \nfoo\n "),
        )
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json('{" "}\n foo\n {" "}'))

    @unittest.skip("pattern_of isn't capable of representing this")
    def test_multiline_indented_one_line(self):
        Transform.pattern_of(
            FTL.TextElement("\n  foo"),
        )

        # Option A.
        # key = {""}
        #     {"  "}foo

        # Option B.
        # key =
        #     {""}
        #       foo

    def test_multiline_indented_two_lines(self):
        pattern = Transform.pattern_of(
            FTL.TextElement("\n  foo\nbar"),
        )
        self.assertEqual(pattern.to_json(), ftl_pattern_to_json('{""}\n    foo\n  bar'))
