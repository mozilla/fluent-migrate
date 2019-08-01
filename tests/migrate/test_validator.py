# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import ast
import unittest

import mock

from fluent.migrate import validator
from fluent.migrate import COPY, COPY_PATTERN


@mock.patch.multiple(
    validator.Validator,
    inspect_migrate=mock.DEFAULT,
)
class TestValidator_inspect(unittest.TestCase):
    def test_missing_migrate(self, inspect_migrate):
        v = validator.Validator("""\
""", 'bug_1.py')
        with self.assertRaises(validator.MigrateNotFoundException):
            v.inspect()
        inspect_migrate.assert_not_called()

    def test_double_migrate(self, inspect_migrate):
        v = validator.Validator("""\
def migrate():
    pass
def migrate():
    pass
""", 'bug_1.py')
        with self.assertRaises(validator.MigrateNotFoundException):
            v.inspect()
        inspect_migrate.assert_called_with(v.ast.body[0], {})

    def test_imports_and_assigns(self, inspect_migrate):
        v = validator.Validator("""\
from mod1.mod2 import func1
from mod1.mod2 import func2 as alias
import mod1.mod3
one = "foo.dtd"
two = one
three = zero
def migrate():
    pass
""", 'bug_1.py')
        details = v.inspect()
        inspect_migrate.assert_called_with(
            v.ast.body[-1], {
                'one': 'foo.dtd',
                'two': 'foo.dtd',
                'func1': 'mod1.mod2.func1',
                'alias': 'mod1.mod2.func2',
                'mod1.mod3': 'mod1.mod3',
            }
        )
        self.assertEqual(details, inspect_migrate.return_value)


@mock.patch(
    'fluent.migrate.validator.MigrateAnalyzer', autospec=True
)
class TestValidator_inspect_migrate(unittest.TestCase):
    def test_bad_args(self, analyzer):
        v = validator.Validator('def migrate():\n pass', 'bug_1.py')
        with self.assertRaises(validator.MigrateNotFoundException):
            v.inspect_migrate(v.ast.body[0], {})
        v = validator.Validator(
            'def migrate(*args, **kwargs):\n pass',
            'bug_1.py'
        )
        with self.assertRaises(validator.MigrateNotFoundException):
            v.inspect_migrate(v.ast.body[0], {})
        v = validator.Validator('def migrate(a, b):\n pass', 'bug_1.py')
        with self.assertRaises(validator.MigrateNotFoundException):
            v.inspect_migrate(v.ast.body[0], {})

    def test_ctx_var(self, Analyzer):
        Analyzer.return_value.sources = set()
        Analyzer.return_value.targets = []
        Analyzer.return_value.issues = []
        v = validator.Validator('def migrate(ctx):\n pass', 'bug_1.py')
        rv = v.inspect_migrate(v.ast.body[0], {})
        Analyzer.return_value.visit.assert_called_with(v.ast.body[0])
        self.assertDictEqual(
            rv,
            {'sources': set(), 'issues': [], 'references': []}
        )


class TestFullName(unittest.TestCase):
    def test_full_name(self):
        orig = 'node.attr1.attr2.attr3'
        m = ast.parse(orig)
        node = m.body[0].value
        self.assertIsInstance(node, ast.Attribute)
        dotted = validator.full_name(node, {})
        self.assertEqual(dotted, orig)

    def test_full_ref_name(self):
        global_assigns = {
            'ref': 'node.attr1'
        }
        orig = 'ref.attr2.attr3'
        m = ast.parse(orig)
        node = m.body[0].value
        self.assertIsInstance(node, ast.Attribute)
        dotted = validator.full_name(node, global_assigns)
        self.assertEqual(dotted, 'node.attr1.attr2.attr3')


@mock.patch.multiple(
    validator.MigrateAnalyzer,
    call_ctx=mock.DEFAULT,
    call_helpers_transforms_from=mock.DEFAULT,
    call_transform=mock.DEFAULT,
)
class TestMigrateAnalyzer_Call(unittest.TestCase):
    def test_other(
        self, call_ctx, call_helpers_transforms_from, call_transform
    ):
        m = ast.parse('qux.baz.bar()')
        v = validator.MigrateAnalyzer('foo', {})
        v.visit(m)
        self.assertListEqual(v.issues, [])
        call_ctx.assert_not_called()
        call_transform.assert_not_called()
        call_helpers_transforms_from.assert_not_called()

    def test_ctx(
        self, call_ctx, call_helpers_transforms_from, call_transform
    ):
        m = ast.parse('foo.bar()')
        v = validator.MigrateAnalyzer('foo', {})
        v.visit(m)
        self.assertListEqual(v.issues, [])
        call_ctx.assert_called_once()
        call_transform.assert_not_called()
        call_helpers_transforms_from.assert_not_called()

    def test_transform(
        self, call_ctx, call_helpers_transforms_from, call_transform
    ):
        m = ast.parse('COPY()')
        v = validator.MigrateAnalyzer('foo', {
            'COPY': 'fluent.migrate.COPY'
        })
        v.visit(m)
        self.assertListEqual(v.issues, [])
        call_ctx.assert_not_called()
        call_transform.assert_called_once()
        call_helpers_transforms_from.assert_not_called()

    def test_helpers(
        self, call_ctx, call_helpers_transforms_from, call_transform
    ):
        m = ast.parse('helpers.transforms_from()')
        v = validator.MigrateAnalyzer('foo', {
            'helpers': 'fluent.migrate.helpers'
        })
        v.visit(m)
        call_ctx.assert_not_called()
        call_transform.assert_not_called()
        call_helpers_transforms_from.assert_called_once()


@mock.patch.multiple(
    validator.MigrateAnalyzer,
    call_maybe_add_localization=mock.DEFAULT,
    call_add_transforms=mock.DEFAULT,
)
class TestMigrateAnalyzer_ctx(unittest.TestCase):
    def test_bad_api(
        self, call_maybe_add_localization, call_add_transforms
    ):
        call = ast.parse('foo.bar()').body[0].value
        self.assertIsInstance(call, ast.Call)
        v = validator.MigrateAnalyzer('foo', {})
        with self.assertRaises(validator.BadContextAPIException):
            v.call_ctx(call)
        call_maybe_add_localization.assert_not_called()
        call_add_transforms.assert_not_called()
        m = ast.parse('foo.bar.baz')
        v = validator.MigrateAnalyzer('foo', {})
        with self.assertRaises(validator.BadContextAPIException):
            v.visit(m)
        call_maybe_add_localization.assert_not_called()
        call_add_transforms.assert_not_called()

    def test_add_transforms(
        self, call_maybe_add_localization, call_add_transforms
    ):
        call = ast.parse('foo.add_transforms()').body[0].value
        self.assertIsInstance(call, ast.Call)
        v = validator.MigrateAnalyzer('foo', {})
        v.call_ctx(call)
        call_maybe_add_localization.assert_not_called()
        call_add_transforms.assert_called_once()

    def test_maybe_add_localization(
        self, call_maybe_add_localization, call_add_transforms
    ):
        call = ast.parse('foo.maybe_add_localization()').body[0].value
        self.assertIsInstance(call, ast.Call)
        v = validator.MigrateAnalyzer('foo', {})
        v.call_ctx(call)
        call_maybe_add_localization.assert_called_once()
        call_add_transforms.assert_not_called()


class TestMigrateAnalyzer_maybe_add_localization(unittest.TestCase):
    def test_bad_args(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse('foo.maybe_add_localization()').body[0].value
        with self.assertRaises(validator.BadContextAPIException):
            v.call_maybe_add_localization(call)

    def test_good_path(self):
        v = validator.MigrateAnalyzer('foo', {
            'src': 'other.dtd',
        })
        call = ast.parse(
            'foo.maybe_add_localization("good.dtd")'
        ).body[0].value
        v.call_maybe_add_localization(call)
        self.assertSetEqual(v.sources, {'good.dtd'})
        # deprecation notice
        self.assertEqual(len(v.issues), 1)
        v.sources.clear()
        v.issues[:] = []
        call = ast.parse(
            'foo.maybe_add_localization(src)'
        ).body[0].value
        v.call_maybe_add_localization(call)
        self.assertSetEqual(v.sources, {'other.dtd'})
        # deprecation notice
        self.assertEqual(len(v.issues), 1)
        v.sources.clear()
        v.issues[:] = []

    def test_bad_path(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse(
            'foo.maybe_add_localization("./good.dtd")'
        ).body[0].value
        v.call_maybe_add_localization(call)
        self.assertSetEqual(v.sources, set())
        # deprecation notice and bad path
        self.assertEqual(len(v.issues), 2)
        v.issues[:] = []
        call = ast.parse(
            'foo.maybe_add_localization(src)'
        ).body[0].value
        v.call_maybe_add_localization(call)
        self.assertSetEqual(v.sources, set())
        # deprecation notice and bad path
        self.assertEqual(len(v.issues), 2)
        v.issues[:] = []


class TestMigrateAnalyzer_add_transforms(unittest.TestCase):
    def test_bad_args(self):
        # add_transforms takes these arguments:
        # reference, target: string or name
        # transform: list or call,
        # possibly keywords for paths
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse('foo.add_transforms()').body[0].value
        v.call_add_transforms(call)
        self.assertEqual(len(v.issues), 1)
        v.issues[:] = []

    def test_paths(self):
        v = validator.MigrateAnalyzer('foo', {
            'src': 'some/fluent.ftl',
            'target': 'some/fluent.ftl',
        })
        call = ast.parse('foo.add_transforms(src, target, [])').body[0].value
        v.call_add_transforms(call)
        self.assertListEqual(v.issues, [])
        self.assertSetEqual(v.targets, {'some/fluent.ftl'})
        v.targets.clear()
        call = ast.parse(
            'foo.add_transforms("some/fluent.ftl", target, [])'
        ).body[0].value
        v.call_add_transforms(call)
        self.assertListEqual(v.issues, [])
        self.assertSetEqual(v.targets, {'some/fluent.ftl'})
        v.targets.clear()
        call = ast.parse(
            'foo.add_transforms(src, "some/fluent.ftl", [])'
        ).body[0].value
        v.call_add_transforms(call)
        self.assertListEqual(v.issues, [])
        self.assertSetEqual(v.targets, {'some/fluent.ftl'})
        v.targets.clear()
        call = ast.parse(
            'foo.add_transforms("some/fluent.ftl", "some/fluent.ftl", [])'
        ).body[0].value
        v.call_add_transforms(call)
        self.assertListEqual(v.issues, [])
        self.assertSetEqual(v.targets, {'some/fluent.ftl'})
        v.targets.clear()

    def test_bad_paths(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse(
            'foo.add_transforms("a.ftl", "b.ftl", [])'
        ).body[0].value
        v.call_add_transforms(call)
        self.assertEqual(len(v.issues), 1)
        self.assertSetEqual(v.targets, set())
        v.issues[:] = []


class TestMigrateAnalyzer_call_transform(unittest.TestCase):
    def test_not_transform(self):
        dotted = 'fluent.migrate.helpers.VARIABLE_REFERENCE'
        v = validator.MigrateAnalyzer('foo', {
            'VARIABLE_REFERENCE': dotted,
        })
        call = ast.parse('''\
from fluent.migrate.helpers import VARIABLE_REFERENCE
VARIABLE_REFERENCE("foo")
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_transform(call, dotted))
        self.assertSetEqual(v.sources, set())
        self.assertListEqual(v.issues, [])

    def test_not_source(self):
        dotted = 'fluent.migrate.transforms.CONCAT'
        v = validator.MigrateAnalyzer('foo', {
            'CONCAT': dotted,
        })
        call = ast.parse('''\
from fluent.migrate.transforms import CONCAT
CONCAT("foo")
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_transform(call, dotted))
        self.assertSetEqual(v.sources, set())
        self.assertListEqual(v.issues, [])

    def test_source(self):
        dotted = 'fluent.migrate.transforms.COPY'
        v = validator.MigrateAnalyzer('foo', {
            'COPY': dotted,
            'src': 'my/fine.dtd',
        })
        call = ast.parse('''\
from fluent.migrate.transforms import COPY
COPY("foo")
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_transform(call, dotted))
        self.assertSetEqual(v.sources, set())
        self.assertEqual(len(v.issues), 1)
        v.issues[:] = []
        call = ast.parse('''\
from fluent.migrate.transforms import COPY
COPY(some, bad, args)
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_transform(call, dotted))
        self.assertSetEqual(v.sources, set())
        self.assertEqual(len(v.issues), 1)
        v.issues[:] = []
        call = ast.parse('''\
from fluent.migrate.transforms import COPY
COPY("my/fine.dtd", "foo")
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_transform(call, dotted))
        self.assertSetEqual(v.sources, {'my/fine.dtd'})
        self.assertListEqual(v.issues, [])
        v.sources.clear()
        call = ast.parse('''\
from fluent.migrate.transforms import COPY
src = "my/fine.dtd"
COPY(src, "foo")
''').body[2].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_transform(call, dotted))
        self.assertSetEqual(v.sources, {'my/fine.dtd'})
        self.assertListEqual(v.issues, [])
        v.sources.clear()


class TestMigrateAnalyzer_call_helpers_transform_from(unittest.TestCase):
    def test_bad_arg(self):
        # we don't support names for literal recipes
        dotted = 'fluent.migrate.helpers.transforms_from'
        v = validator.MigrateAnalyzer('foo', {
            'transforms_from': dotted,
            'code': 'foo = bar',
        })
        call = ast.parse('''\
from fluent.migrate.helpers import transforms_from
transforms_from(code)
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_helpers_transforms_from(call))
        self.assertSetEqual(v.sources, set())
        self.assertEqual(len(v.issues), 1)

    def test_parse_error(self):
        dotted = 'fluent.migrate.helpers.transforms_from'
        v = validator.MigrateAnalyzer('foo', {
            'transforms_from': dotted,
        })
        call = ast.parse('''\
from fluent.migrate.helpers import transforms_from
transforms_from("""
k3 = {COPY(src, "other_key)}
""", src='other.dtd')
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_helpers_transforms_from(call))
        self.assertSetEqual(v.sources, set())
        self.assertEqual(len(v.issues), 1)
        v.issues[:] = []

    def test_bad_src_var(self):
        dotted = 'fluent.migrate.helpers.transforms_from'
        v = validator.MigrateAnalyzer('foo', {
            'transforms_from': dotted,
        })
        call = ast.parse('''\
from fluent.migrate.helpers import transforms_from
transforms_from("""
k3 = {COPY(one_src, "key")}
""", one_src=one_src)
''').body[1].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_helpers_transforms_from(call))
        self.assertSetEqual(v.sources, set())
        self.assertEqual(len(v.issues), 1)
        v.issues[:] = []

    def test_success(self):
        dotted = 'fluent.migrate.helpers.transforms_from'
        v = validator.MigrateAnalyzer('foo', {
            'transforms_from': dotted,
            'one_src': 'one.dtd',
        })
        call = ast.parse('''\
from fluent.migrate.helpers import transforms_from
one_src = "one.dtd"
transforms_from("""
k1 = bar
k2 = {COPY("one.dtd", "string_key")}
k3 = {COPY(two_src, "other_key")}
""", one_src=one_src, two_src='other.dtd')
''').body[2].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsNone(v.call_helpers_transforms_from(call))
        self.assertSetEqual(v.sources, {'one.dtd', 'other.dtd'})
        self.assertListEqual(v.issues, [])


class TestMigrateAnalyzer_check_arguments(unittest.TestCase):
    def test_empty(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse('foo()').body[0].value
        self.assertTrue(v.check_arguments(call, list()))
        self.assertTrue(v.check_arguments(call, list(), check_kwargs=False))
        self.assertTrue(v.check_arguments(call, list(), allow_more=True))

    def test_types(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse('foo("s")').body[0].value
        self.assertTrue(v.check_arguments(call, (ast.Str,)))
        self.assertTrue(v.check_arguments(call, ((ast.Str, ast.Name),)))
        self.assertFalse(v.check_arguments(call, (ast.Name,)))

    def test_argument_count(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse('foo("s")').body[0].value
        self.assertFalse(v.check_arguments(call, (ast.Str, ast.Str)))
        self.assertFalse(
            v.check_arguments(call, (ast.Str, ast.Str), allow_more=True)
        )
        self.assertFalse(v.check_arguments(call, tuple()))
        self.assertTrue(v.check_arguments(call, tuple(), allow_more=True))

    def test_kwargs(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse('foo("s", some="stuff")').body[0].value
        self.assertFalse(v.check_arguments(call, (ast.Str,)))
        self.assertTrue(
            v.check_arguments(call, (ast.Str,), check_kwargs=False)
        )
        call = ast.parse('foo("s", **kwargs)').body[0].value
        self.assertFalse(v.check_arguments(call, (ast.Str,)))
        self.assertTrue(
            v.check_arguments(call, (ast.Str,), check_kwargs=False)
        )

    def test_starargs(self):
        v = validator.MigrateAnalyzer('foo', {})
        call = ast.parse('foo(*args)').body[0].value
        self.assertFalse(v.check_arguments(call, (ast.Str,)))
        self.assertFalse(
            v.check_arguments(call, (ast.Str,), check_kwargs=False)
        )
        self.assertFalse(v.check_arguments(call, (ast.Str,), allow_more=True))


class TestTransformsInspector(unittest.TestCase):
    def test_good_copy(self):
        node = COPY('foo/bar.dtd', 'key1')
        ti = validator.TransformsInspector()
        ti.visit(node)
        self.assertListEqual(ti.issues, [])
        self.assertSetEqual(ti.sources, {'foo/bar.dtd'})

    def test_copy_with_issue(self):
        node = COPY('./foo/bar.dtd', 'key1')
        ti = validator.TransformsInspector()
        ti.visit(node)
        self.assertListEqual(ti.issues, [
            'Source "./foo/bar.dtd" needs to be a normalized path'
        ])
        self.assertSetEqual(ti.sources, set())

    def test_good_copy_pattern(self):
        node = COPY_PATTERN('foo/bar.ftl', 'key1')
        ti = validator.TransformsInspector()
        ti.visit(node)
        self.assertListEqual(ti.issues, [])
        self.assertSetEqual(ti.sources, {'foo/bar.ftl'})

    def test_copy_pattern_with_issue(self):
        node = COPY_PATTERN('./foo/bar.ftl', 'key1')
        ti = validator.TransformsInspector()
        ti.visit(node)
        self.assertListEqual(ti.issues, [
            'Source "./foo/bar.ftl" needs to be a normalized path'
        ])
        self.assertSetEqual(ti.sources, set())
