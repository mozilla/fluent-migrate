import unittest

import fluent.syntax.ast as FTL
from fluent.migrate.util import fold, ftl_resource_to_ast, skeleton
from fluent.migrate.transforms import CONCAT, COPY, REPLACE, Source


def get_source(acc, cur):
    if isinstance(cur, Source):
        return acc + ((cur.path, cur.key),)
    return acc


class TestReduce(unittest.TestCase):
    def test_copy_value(self):
        node = FTL.Message(
            id=FTL.Identifier('key'),
            value=COPY('path', 'key')
        )

        self.assertEqual(
            fold(get_source, node, ()),
            (('path', 'key'),)
        )

    def test_copy_traits(self):
        node = FTL.Message(
            id=FTL.Identifier('key'),
            attributes=[
                FTL.Attribute(
                    FTL.Identifier('trait1'),
                    value=COPY('path1', 'key1')
                ),
                FTL.Attribute(
                    FTL.Identifier('trait2'),
                    value=COPY('path2', 'key2')
                )
            ]
        )

        self.assertEqual(
            fold(get_source, node, ()),
            (('path1', 'key1'), ('path2', 'key2'))
        )

    def test_copy_concat(self):
        node = FTL.Message(
            FTL.Identifier('hello'),
            value=CONCAT(
                COPY('path1', 'key1'),
                COPY('path2', 'key2')
            )
        )

        self.assertEqual(
            fold(get_source, node, ()),
            (('path1', 'key1'), ('path2', 'key2'))
        )

    def test_copy_in_replace(self):
        node = FTL.Message(
            FTL.Identifier('hello'),
            value=REPLACE(
                'path1',
                'key1',
                {
                    "foo": COPY('path2', 'key2')
                }
            )
        )

        self.assertEqual(
            fold(get_source, node, ()),
            (('path2', 'key2'), ('path1', 'key1'))
        )


class TestSkeleton(unittest.TestCase):
    def test_skeleton(self):
        resource = ftl_resource_to_ast('''
        # License comment

        ### resource comment

        just-val = something
        val-and-attr = else
            .with = an attribute
        -term = always
        ''')
        new_skeleton = [skeleton(node) for node in resource.body]
        for orig, new in zip(resource.body, new_skeleton):
            self.assertNotEqual(orig, new)
            if isinstance(new, (FTL.Message, FTL.Term)):
                self.assertFalse(orig.equals(new))
                self.assertIsNone(new.value)
                self.assertListEqual(new.attributes, [])
            else:
                self.assertTrue(orig.equals(new))
