import unittest

import fluent.syntax.ast as FTL
from fluent.migrate.helpers import MESSAGE_REFERENCE
from fluent.migrate.transforms import CONCAT, COPY


class TestConcatSingleChild(unittest.TestCase):
    def test_copy_trim_default(self):
        transform = CONCAT(
            COPY("test.properties", "hello"),
        )
        self.assertEqual(transform.elements[0].trim, None)

    def test_copy_trim_false(self):
        transform = CONCAT(
            COPY("test.properties", "hello", trim=False),
        )
        self.assertEqual(transform.elements[0].trim, False)

    def test_copy_trim_true(self):
        transform = CONCAT(
            COPY("test.properties", "hello", trim=True),
        )
        self.assertEqual(transform.elements[0].trim, True)

    def test_text_element(self):
        CONCAT(
            FTL.TextElement("Hello"),
        )

    def test_expression(self):
        CONCAT(
            MESSAGE_REFERENCE("hello"),
        )


class TestConcatMultipleChildren(unittest.TestCase):
    def test_copy_multiple(self):
        transform = CONCAT(
            COPY("test.properties", "hello"),
            COPY("test.properties", "hello", trim=False),
            COPY("test.properties", "hello", trim=True),
        )
        self.assertEqual(transform.elements[0].trim, False)
        self.assertEqual(transform.elements[1].trim, False)
        self.assertEqual(transform.elements[2].trim, True)

    def test_mixed(self):
        CONCAT(
            COPY("test.properties", "hello"),
            FTL.TextElement("Hello"),
            MESSAGE_REFERENCE("hello"),
        )


if __name__ == "__main__":
    unittest.main()
