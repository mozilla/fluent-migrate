# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
import six
from six.moves import zip_longest

import fluent.syntax.ast as FTL
from fluent.migrate.helpers import transforms_from
from fluent.migrate.transforms import CONCAT, COPY
from fluent.migrate.errors import NotSupportedError, InvalidTransformError


class TestTransformsFrom(unittest.TestCase):
    def assert_transforms_equal(self, parsed, expected):
        return self.assertTrue(
            all(actual.equals(ast) for actual, ast
                in zip_longest(parsed, expected)),
            """\
Parsed transforms do not match the expected transforms.

------------------------------ Parsed --------------------------------
{}

----------------------------- Expected -------------------------------
{}
"""         .format(
                [msg.to_json() for msg in parsed],
                [msg.to_json() for msg in expected]))

    def test_text_element(self):
        parsed = transforms_from("""
new-key = Hardcoded value.
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    FTL.TextElement("Hardcoded value.")
                )
            )
        ])

    def test_two_messages(self):
        parsed = transforms_from("""
key-one = Hardcoded value.
key-two = Another value.
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("key-one"),
                value=CONCAT(
                    FTL.TextElement("Hardcoded value.")
                )
            ),
            FTL.Message(
                id=FTL.Identifier("key-two"),
                value=CONCAT(
                    FTL.TextElement("Another value.")
                )
            )
        ])

    def test_message_reference(self):
        parsed = transforms_from("""
new-key = Prefix { message-reference } postfix.
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    FTL.TextElement("Prefix "),
                    FTL.Placeable(
                        FTL.MessageReference(
                            FTL.Identifier("message-reference")
                        )
                    ),
                    FTL.TextElement(" postfix.")
                )
            )
        ])

    def test_external_argument(self):
        parsed = transforms_from("""
new-key = Prefix { $argument } postfix.
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    FTL.TextElement("Prefix "),
                    FTL.Placeable(
                        FTL.VariableReference(
                            FTL.Identifier("argument")
                        )
                    ),
                    FTL.TextElement(" postfix.")
                )
            )
        ])

    def test_select_expression(self):
        parsed = transforms_from("""
new-key = Prefix { PLATFORM() ->
        [macos] macOS
       *[other] Other
    } postfix.
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    FTL.TextElement("Prefix "),
                    FTL.Placeable(
                        FTL.SelectExpression(
                            selector=FTL.CallExpression(
                                callee=FTL.Function("PLATFORM")
                            ),
                            variants=[
                                FTL.Variant(
                                    key=FTL.VariantName('macos'),
                                    default=False,
                                    value=CONCAT(
                                        FTL.TextElement("macOS")
                                    )
                                ),
                                FTL.Variant(
                                    key=FTL.VariantName('other'),
                                    default=True,
                                    value=CONCAT(
                                        FTL.TextElement("Other")
                                    )
                                ),
                            ]
                        )
                    ),
                    FTL.TextElement(" postfix.")
                )
            )
        ])

    def test_attribute(self):
        parsed = transforms_from("""
new-key =
    .attr = Attribute value
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                attributes=[
                    FTL.Attribute(
                        id=FTL.Identifier("attr"),
                        value=CONCAT(
                            FTL.TextElement("Attribute value"),
                        )
                    )
                ]
            )
        ])

    def test_block_value(self):
        parsed = transforms_from("""
new-key =
    Block value
    continued.
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    FTL.TextElement("Block value\ncontinued.")
                )
            )
        ])

    def test_copy_in_value(self):
        parsed = transforms_from("""
new-key = { COPY("path", "key") }
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    COPY("path", "key")
                )
            )
        ])

    def test_trim_copy_in_value(self):
        parsed = transforms_from("""
new-key = { COPY("path", "key", trim: "True") }
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    COPY("path", "key", trim=True)
                )
            )
        ])

    def test_copy_in_select_expression(self):
        parsed = transforms_from("""
new-key =
    { PLATFORM() ->
        [macos] { COPY("path", "key.mac") }
       *[other] { COPY("path", "key.other") }
    }
""")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    FTL.Placeable(
                        FTL.SelectExpression(
                            selector=FTL.CallExpression(
                                callee=FTL.Function("PLATFORM")
                            ),
                            variants=[
                                FTL.Variant(
                                    key=FTL.VariantName('macos'),
                                    default=False,
                                    value=CONCAT(
                                        COPY("path", "key.mac")
                                    )
                                ),
                                FTL.Variant(
                                    key=FTL.VariantName('other'),
                                    default=True,
                                    value=CONCAT(
                                        COPY("path", "key.other")
                                    )
                                ),
                            ]
                        )
                    )
                )
            )
        ])

    def test_implicit_transform(self):
        pattern = "runs implicitly"
        with six.assertRaisesRegex(self, NotSupportedError, pattern):
            transforms_from("""
new-key = { CONCAT("a", "b") }
""")

    def test_forbidden_transform(self):
        pattern = "requires additional logic"
        with six.assertRaisesRegex(self, NotSupportedError, pattern):
            transforms_from("""
new-key = { REPLACE() }
""")

    def test_broken_transform(self):
        pattern = "contains parse error"
        with six.assertRaisesRegex(self, InvalidTransformError, pattern):
            transforms_from("""
new-key = { COPY('path', 'key') }
""")

    def test_substitution(self):
        parsed = transforms_from("""
new-key = { COPY(from_path, "key") }
""", from_path="path")

        self.assert_transforms_equal(parsed, [
            FTL.Message(
                id=FTL.Identifier("new-key"),
                value=CONCAT(
                    COPY("path", "key")
                )
            )
        ])

    def test_unknown_substitution_name(self):
        pattern = "Unknown substitution in COPY: unknown_path"
        with six.assertRaisesRegex(self, InvalidTransformError, pattern):
            transforms_from("""
new-key = { COPY(unknown_path, "key") }
""")

    def test_invalid_argument_type(self):
        pattern = "Invalid argument passed to COPY: VariableReference"
        with six.assertRaisesRegex(self, InvalidTransformError, pattern):
            transforms_from("""
new-key = { COPY($invalid_type, "key") }
""")
