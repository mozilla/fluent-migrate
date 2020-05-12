# coding=utf8
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
import six
from compare_locales.parser import PropertiesParser, DTDParser

import fluent.syntax.ast as FTL
from fluent.migrate.errors import NotSupportedError
from fluent.migrate.transforms import (
    LegacySource, COPY, PLURALS, REPLACE,
    COPY_PATTERN,
)
from fluent.migrate.util import parse
from fluent.migrate.helpers import VARIABLE_REFERENCE


class TestNotSupportedError(unittest.TestCase):
    def test_source(self):
        pattern = ('Please use COPY_PATTERN to migrate from Fluent files')
        with six.assertRaisesRegex(self, NotSupportedError, pattern):
            LegacySource('test.ftl', 'foo')

    def test_copy(self):
        pattern = ('Please use COPY_PATTERN to migrate from Fluent files')
        with six.assertRaisesRegex(self, NotSupportedError, pattern):
            COPY('test.ftl', 'foo')

    def test_plurals(self):
        pattern = ('Please use COPY_PATTERN to migrate from Fluent files')
        with six.assertRaisesRegex(self, NotSupportedError, pattern):
            PLURALS(
                'test.ftl',
                'deleteAll',
                VARIABLE_REFERENCE('num')
            )

    def test_replace(self):
        pattern = ('Please use COPY_PATTERN to migrate from Fluent files')
        with six.assertRaisesRegex(self, NotSupportedError, pattern):
            REPLACE(
                'test.ftl',
                'hello',
                {
                    '#1': VARIABLE_REFERENCE('username')
                }
            )

    def test_copy_pattern(self):
        pattern = ('Please use COPY to migrate from legacy files')
        with six.assertRaisesRegex(self, NotSupportedError, pattern):
            COPY_PATTERN('test.properties', 'foo')
        self.assertIsNotNone(COPY_PATTERN('test.ftl', 'foo'))
        self.assertIsNotNone(COPY_PATTERN('test.ftl', 'foo.bar'))
        self.assertIsNotNone(COPY_PATTERN('test.ftl', '-foo'))
        term_attr_pattern = ('Cannot migrate from Term Attributes')
        with six.assertRaisesRegex(self, NotSupportedError, term_attr_pattern):
            COPY_PATTERN('test.ftl', '-foo.bar')


class MockContext(unittest.TestCase):
    def get_legacy_source(self, _path, key):
        # Ignore _path (test.properties), get translations from self.strings.
        return self.strings[key].val


class TestProperties(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            foo = Foo
            value-empty =
            value-whitespace =    \n\

            unicode-all = \\u0040
            unicode-start = \\u0040Foo
            unicode-middle = Foo\\u0040Bar
            unicode-end = Foo\\u0040

            space-all = \\u0020
            space-start = \\u0020Foo
            space-middle = Foo\\u0020Bar
            space-end = Foo\\u0020

            newline = \\nnext up is a \\n

            html-entity = &lt;&#x21E7;&#x2318;K&gt;
        ''')

    def test_simple_text(self):
        source = LegacySource('test.properties', 'foo')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

    def test_empty_value(self):
        source = LegacySource('test.properties', 'value-empty')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

    def test_whitespace_value(self):
        source = LegacySource('test.properties', 'value-whitespace')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

    def test_escape_unicode_all(self):
        source = LegacySource('test.properties', 'unicode-all')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '@')

    def test_escape_unicode_start(self):
        source = LegacySource('test.properties', 'unicode-start')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '@Foo')

    def test_escape_unicode_middle(self):
        source = LegacySource('test.properties', 'unicode-middle')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo@Bar')

    def test_escape_unicode_end(self):
        source = LegacySource('test.properties', 'unicode-end')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo@')

    def test_space_all(self):
        source = LegacySource('test.properties', 'space-all')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

        source = LegacySource('test.properties', 'space-all', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

        source = LegacySource('test.properties', 'space-all', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, ' ')

    def test_space_start(self):
        source = LegacySource('test.properties', 'space-start')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

        source = LegacySource('test.properties', 'space-start', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

        source = LegacySource('test.properties', 'space-start', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, ' Foo')

    def test_space_middle(self):
        source = LegacySource('test.properties', 'space-middle')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo Bar')

        source = LegacySource('test.properties', 'space-middle', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo Bar')

        source = LegacySource('test.properties', 'space-middle', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo Bar')

    def test_space_end(self):
        source = LegacySource('test.properties', 'space-end')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

        source = LegacySource('test.properties', 'space-end', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

        source = LegacySource('test.properties', 'space-end', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo ')

    def test_newline(self):
        source = LegacySource('test.properties', 'newline')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'next up is a')

        source = LegacySource('test.properties', 'newline', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'next up is a')

        source = LegacySource('test.properties', 'newline', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '\nnext up is a \n')

    def test_html_entity(self):
        source = LegacySource('test.properties', 'html-entity')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&lt;&#x21E7;&#x2318;K&gt;')


class TestDTD(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY foo "Foo">

            <!ENTITY valueEmpty "">
            <!ENTITY valueWhitespace "    ">

            <!ENTITY multiline1 "Foo  \x20
    Bar
">
            <!ENTITY multiline2 "
    Foo  \x20
      Bar
    ">

            <!ENTITY unicodeEscape "Foo\\u0020Bar">

            <!ENTITY named "&amp;">
            <!ENTITY decimal "&#38;">
            <!ENTITY shorthexcode "&#x26;">
            <!ENTITY longhexcode "&#x0026;">
            <!ENTITY unknown "&unknownEntity;">
        ''')

    def test_simple_text(self):
        source = LegacySource('test.dtd', 'foo')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

    def test_empty_value(self):
        source = LegacySource('test.dtd', 'valueEmpty')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

    def test_whitespace(self):
        source = LegacySource('test.dtd', 'valueWhitespace')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

        source = LegacySource('test.dtd', 'valueWhitespace', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

        source = LegacySource('test.dtd', 'valueWhitespace', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '    ')

    def test_multiline1(self):
        source = LegacySource('test.dtd', 'multiline1')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo\nBar')

        source = LegacySource('test.dtd', 'multiline1', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo\nBar')

        source = LegacySource('test.dtd', 'multiline1', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo   \n    Bar\n')

    def test_multiline2(self):
        source = LegacySource('test.dtd', 'multiline2')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo\nBar')

        source = LegacySource('test.dtd', 'multiline2', trim=True)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo\nBar')

        source = LegacySource('test.dtd', 'multiline2', trim=False)
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '\n    Foo   \n      Bar\n    ')

    def test_backslash_unicode_escape(self):
        source = LegacySource('test.dtd', 'unicodeEscape')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo\\u0020Bar')

    def test_named_entity(self):
        source = LegacySource('test.dtd', 'named')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_decimal_entity(self):
        source = LegacySource('test.dtd', 'decimal')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_shorthex_entity(self):
        source = LegacySource('test.dtd', 'shorthexcode')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_longhex_entity(self):
        source = LegacySource('test.dtd', 'longhexcode')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_unknown_entity(self):
        source = LegacySource('test.dtd', 'unknown')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&unknownEntity;')
