import unittest

from fluent.migrate.transforms import COPY


class TestCopy(unittest.TestCase):
    def test_trim(self):
        transform = COPY("test.properties", "foo")
        self.assertEqual(transform.trim, None)

        transform = COPY("test.properties", "foo", trim=True)
        self.assertEqual(transform.trim, True)

        transform = COPY("test.properties", "foo", trim=False)
        self.assertEqual(transform.trim, False)


if __name__ == "__main__":
    unittest.main()
