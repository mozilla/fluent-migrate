import unittest

from fluent.migrate.context import MigrationContext
from fluent.migrate.transforms import TransformPattern
from fluent.migrate.util import ftl_pattern_to_json
from fluent.migrate import validator
from fluent.syntax import ast as FTL


simple_ref = '''
simple = message
'''


class TextReplace(TransformPattern):
    def visit_TextElement(self, node):
        node.value = node.value.replace('e', 'a')
        return node


class TestTransformPattern(unittest.TestCase):
    def setUp(self):
        self.ctx = MigrationContext('en', None, None)
        self.ctx.localization_resources['file.ftl'] = \
            self.ctx.fluent_parser.parse(simple_ref)
        self.ti = validator.TransformsInspector()

    def test_no_op(self):
        transform = TransformPattern('file.ftl', 'simple')
        result = transform(self.ctx)
        self.assertEqual(result.to_json(), ftl_pattern_to_json('message'))
        # Make sure the validator accepts TransformPattern subclasses.
        self.ti.visit(transform)
        self.assertListEqual(self.ti.issues, [])

    def test_text(self):
        transform = TextReplace('file.ftl', 'simple')
        result = transform(self.ctx)
        self.assertEqual(result.to_json(), ftl_pattern_to_json('massaga'))


select_ref = '''
selected = {$foo ->
    [one] This is one.
   *[two] This is two.
}
'''


class VariantPicker(TransformPattern):
    def __init__(self, path, key, variant, exclude=False):
        super().__init__(path, key)
        self.variant = variant
        self.exclude = exclude

    def visit_SelectExpression(self, node):
        found = None
        for variant in node.variants:
            if isinstance(variant.key, FTL.Identifier):
                key = variant.key.name
            else:
                key = variant.key.value
            if key == self.variant:
                found = variant
                break
        if found is not None:
            if not self.exclude:
                return self.visit(found.value)
            if not found.default:
                node.variants.remove(found)
                if len(node.variants) == 1:
                    return self.visit(node.variants[0].value)
        return self.generic_visit(node)


class TestVariantPicker(unittest.TestCase):
    def setUp(self):
        self.ctx = MigrationContext('en', None, None)
        self.ctx.localization_resources['file.ftl'] = \
            self.ctx.fluent_parser.parse(select_ref)

    def test_select_one(self):
        transform = VariantPicker('file.ftl', 'selected', 'one')
        result = transform(self.ctx)
        self.assertEqual(result.to_json(), ftl_pattern_to_json("This is one."))

    def test_exclude_one(self):
        transform = VariantPicker('file.ftl', 'selected', 'one', exclude=True)
        result = transform(self.ctx)
        self.assertEqual(result.to_json(), ftl_pattern_to_json("This is two."))

    def test_select_two(self):
        transform = VariantPicker('file.ftl', 'selected', 'two')
        result = transform(self.ctx)
        self.assertEqual(result.to_json(), ftl_pattern_to_json("This is two."))

    def test_exclude_two(self):
        # With two being the default variant, it might be used for three.
        # Thus, don't remove it.
        transform = VariantPicker('file.ftl', 'selected', 'two', exclude=True)
        result = transform(self.ctx)
        self.assertEqual(
            result.to_json(),
            ftl_pattern_to_json(select_ref.split(" = ")[1])
        )
