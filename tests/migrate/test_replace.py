import unittest
from compare_locales.parser import PropertiesParser

import fluent.syntax.ast as FTL
from fluent.migrate.util import parse, ftl_pattern_to_json
from fluent.migrate.helpers import VARIABLE_REFERENCE
from fluent.migrate.transforms import REPLACE
from fluent.migrate.evaluator import Evaluator


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_legacy_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val

    def evaluate(self, node):
        return self.evaluator.visit(node)


class TestReplace(MockContext):
    def setUp(self):
        self.evaluator = Evaluator(self)
        self.strings = parse(
            PropertiesParser,
            """
            empty =
            hello = Hello, #1!
            welcome = Welcome, #1, to #2!
            first = #1 Bar
            last = Foo #1
            multiple = First: #1 Second: #1
            interleaved = #1 #2 #1 #2
        """,
        )

    def test_trim(self):
        transform = REPLACE("test.properties", "foo", {})
        self.assertEqual(transform.trim, None)

        transform = REPLACE("test.properties", "foo", {}, trim=True)
        self.assertEqual(transform.trim, True)

        transform = REPLACE("test.properties", "foo", {}, trim=False)
        self.assertEqual(transform.trim, False)

    def test_replace_empty(self):
        transform = REPLACE(
            "test.properties", "empty", {"#1": VARIABLE_REFERENCE("arg")}
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json('{""}')
        )

    def test_replace_one(self):
        transform = REPLACE(
            "test.properties", "hello", {"#1": VARIABLE_REFERENCE("username")}
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("Hello, { $username }!"),
        )

    def test_replace_two(self):
        transform = REPLACE(
            "test.properties",
            "welcome",
            {"#1": VARIABLE_REFERENCE("username"), "#2": VARIABLE_REFERENCE("appname")},
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("Welcome, { $username }, to { $appname }!"),
        )

    def test_replace_too_many(self):
        transform = REPLACE(
            "test.properties",
            "welcome",
            {
                "#1": VARIABLE_REFERENCE("username"),
                "#2": VARIABLE_REFERENCE("appname"),
                "#3": VARIABLE_REFERENCE("extraname"),
            },
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("Welcome, { $username }, to { $appname }!"),
        )

    def test_replace_too_few(self):
        transform = REPLACE(
            "test.properties", "welcome", {"#1": VARIABLE_REFERENCE("username")}
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("Welcome, { $username }, to #2!"),
        )

    def test_replace_first(self):
        transform = REPLACE(
            "test.properties", "first", {"#1": VARIABLE_REFERENCE("foo")}
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("{ $foo } Bar")
        )

    def test_replace_last(self):
        transform = REPLACE(
            "test.properties", "last", {"#1": VARIABLE_REFERENCE("bar")}
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("Foo { $bar }")
        )

    def test_replace_multiple(self):
        transform = REPLACE(
            "test.properties", "multiple", {"#1": VARIABLE_REFERENCE("var")}
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("First: { $var } Second: { $var }"),
        )

    def test_replace_interleaved(self):
        transform = REPLACE(
            "test.properties",
            "interleaved",
            {"#1": VARIABLE_REFERENCE("foo"), "#2": VARIABLE_REFERENCE("bar")},
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("{ $foo } { $bar } { $foo } { $bar }"),
        )

    def test_replace_with_placeable(self):
        transform = REPLACE(
            "test.properties",
            "hello",
            {"#1": FTL.Placeable(VARIABLE_REFERENCE("user"))},
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("Hello, { $user }!")
        )

    def test_replace_with_text_element(self):
        transform = REPLACE("test.properties", "hello", {"#1": FTL.TextElement("you")})

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("Hello, you!")
        )

    def test_replace_with_pattern(self):
        transform = REPLACE(
            "test.properties",
            "hello",
            {
                "#1": FTL.Pattern(
                    elements=[
                        FTL.TextElement("<img> "),
                        FTL.Placeable(VARIABLE_REFERENCE("user")),
                    ]
                )
            },
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("Hello, <img> { $user }!"),
        )


class TestNormalize(MockContext):
    def setUp(self):
        self.evaluator = Evaluator(self)
        self.strings = parse(
            PropertiesParser,
            """
            empty =
            simple = %1$S
            double = %2$S %1$S
            one = %d
            two = %d %S
            hidden = %2$S%1$0.S
            hidden_w_out = %0.S%S
            escaped = %d%%
        """,
        )

    def test_empty(self):
        transform = REPLACE(
            "test.properties",
            "empty",
            {"%1$S": FTL.Placeable(VARIABLE_REFERENCE("user"))},
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json('{""}')
        )

    def test_simple(self):
        transform = REPLACE(
            "test.properties",
            "simple",
            {"%1$S": FTL.Placeable(VARIABLE_REFERENCE("user"))},
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("{ $user }")
        )

    def test_double(self):
        transform = REPLACE(
            "test.properties",
            "double",
            {
                "%1$S": FTL.Placeable(VARIABLE_REFERENCE("user")),
                "%2$S": FTL.Placeable(VARIABLE_REFERENCE("count")),
            },
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("{ $count } { $user }"),
        )

    def test_one(self):
        transform = REPLACE(
            "test.properties",
            "one",
            {
                "%1$d": FTL.Placeable(VARIABLE_REFERENCE("count")),
                "%2$S": FTL.Placeable(VARIABLE_REFERENCE("user")),
            },
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("{ $count }")
        )

    def test_two(self):
        transform = REPLACE(
            "test.properties",
            "two",
            {
                "%1$d": FTL.Placeable(VARIABLE_REFERENCE("count")),
                "%2$S": FTL.Placeable(VARIABLE_REFERENCE("user")),
            },
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("{ $count } { $user }"),
        )

    def test_two_default_normalize(self):
        transform = REPLACE(
            "test.properties",
            "two",
            {
                "%1$d": FTL.Placeable(VARIABLE_REFERENCE("count")),
                "%2$S": FTL.Placeable(VARIABLE_REFERENCE("user")),
            },
        )

        self.assertEqual(
            self.evaluate(transform).to_json(),
            ftl_pattern_to_json("{ $count } { $user }"),
        )

    def test_hidden(self):
        transform = REPLACE(
            "test.properties",
            "hidden",
            {
                "%1$S": FTL.Placeable(VARIABLE_REFERENCE("user")),
                "%2$S": FTL.Placeable(VARIABLE_REFERENCE("count")),
            },
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("{ $count }")
        )

    def test_hidden_w_out(self):
        transform = REPLACE(
            "test.properties",
            "hidden_w_out",
            {
                "%1$S": FTL.Placeable(VARIABLE_REFERENCE("user")),
                "%2$S": FTL.Placeable(VARIABLE_REFERENCE("count")),
            },
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("{ $count }")
        )

    def test_escaped(self):
        transform = REPLACE(
            "test.properties",
            "escaped",
            {
                "%1$d": FTL.Placeable(VARIABLE_REFERENCE("count")),
            },
            normalize_printf=True,
        )

        self.assertEqual(
            self.evaluate(transform).to_json(), ftl_pattern_to_json("{ $count }%")
        )


if __name__ == "__main__":
    unittest.main()
