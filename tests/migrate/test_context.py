import os
import logging
import unittest

import fluent.syntax.ast as FTL
from fluent.migrate.errors import (
    EmptyLocalizationError,
    UnreadableReferenceError,
)
from fluent.migrate.util import ftl, ftl_resource_to_json, to_json
from fluent.migrate.context import MigrationContext
from fluent.migrate.transforms import CONCAT, COPY


def here(*parts):
    dirname = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dirname, *parts)


class TestMigrationContext_AddTransforms(unittest.TestCase):
    def setUp(self):
        self.ctx = MigrationContext(
            locale='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def test_hardcoded_node(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('about'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        self.assertSetEqual(
            self.ctx.dependencies[('aboutDownloads.ftl', 'about')],
            set()
        )
        self.assertTrue(
            self.ctx.in_changeset(
                set(),
                set(),
                'aboutDownloads.ftl', 'about'
            )
        )

    def test_no_reference(self):
        self.ctx.reference_dir = None
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
        ])
        ref_ast = self.ctx.reference_resources.get('aboutDownloads.ftl')
        self.assertIsNotNone(ref_ast)
        self.assertEqual(len(ref_ast.body), 1)
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('header'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.header'
                )
            ),
        ])
        self.assertEqual(
            id(self.ctx.reference_resources.get('aboutDownloads.ftl')),
            id(ref_ast)
        )
        self.assertEqual(len(ref_ast.body), 2)


class TestMigrationContext(unittest.TestCase):
    def setUp(self):
        self.ctx = MigrationContext(
            locale='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def test_hardcoded_node(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('about'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        about = Hardcoded Value
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_merge_single_message(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
        ])

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_merge_one_changeset(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('header'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.header'
                )
            ),
        ])

        changeset = {
            ('aboutDownloads.dtd', 'aboutDownloads.title'),
            ('aboutDownloads.dtd', 'aboutDownloads.header')
        }

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
        header = Twoje pobrane pliki
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(changeset)),
            expected
        )

    def test_merge_two_changesets(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('header'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.header'
                )
            ),
        ])

        changeset_a = {
            ('aboutDownloads.dtd', 'aboutDownloads.title'),
        }

        changeset_b = {
            ('aboutDownloads.dtd', 'aboutDownloads.header')
        }

        expected_a = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
            ''')
        }

        expected_b = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
        header = Twoje pobrane pliki
            ''')
        }

        merged_a = to_json(self.ctx.merge_changeset(changeset_a))
        self.assertDictEqual(merged_a, expected_a)

        merged_b = to_json(self.ctx.merge_changeset(changeset_b))
        self.assertDictEqual(merged_b, expected_b)

    def test_serialize_changeset(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('header'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.header'
                )
            ),
        ])

        changesets = [
            {
                ('aboutDownloads.dtd', 'aboutDownloads.title'),
            },
            {
                ('aboutDownloads.dtd', 'aboutDownloads.header')
            }
        ]

        expected = iter([
            {
                'aboutDownloads.ftl': ftl('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
                ''')
            },
            {
                'aboutDownloads.ftl': ftl('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
        header = Twoje pobrane pliki
                ''')
            }
        ])

        for changeset in changesets:
            serialized = self.ctx.serialize_changeset(changeset)
            self.assertEqual(serialized, next(expected))

    def test_fluent_source(self):
        self.ctx.maybe_add_localization('existing.ftl')
        bar = self.ctx.get_fluent_source_pattern('existing.ftl', 'bar')
        self.assertIsInstance(bar, FTL.Pattern)

    def test_bilingual_translated(self):
        self.ctx.add_transforms('bilingual.ftl', 'bilingual.ftl', [
            FTL.Message(
                id=FTL.Identifier('two'),
                value=COPY(
                    'bilingual.po',
                    ('translated', None)
                )
            ),
        ])
        expected = {
            'bilingual.ftl': ftl_resource_to_json('''
            # License

            # This was translated
            two = foopy
            ''')
        }
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(None)),
            expected
        )

    def test_bilingual_untranslated(self):
        self.ctx.add_transforms('bilingual.ftl', 'bilingual.ftl', [
            FTL.Message(
                id=FTL.Identifier('one'),
                value=COPY(
                    'bilingual.po',
                    ('untranslated', None)
                )
            ),
        ])
        expected = {}
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(None)),
            expected
        )

    def test_bilingual_enforce_translated(self):
        self.ctx.enforce_translated = True
        self.ctx.add_transforms('bilingual.ftl', 'bilingual.ftl', [
            FTL.Message(
                id=FTL.Identifier('one'),
                value=COPY(
                    'bilingual.po',
                    ('untranslated', None)
                )
            ),
        ])
        expected = {
            'bilingual.ftl': ftl_resource_to_json('''
            # License

            # This was untranslated
            one = untranslated
            ''')
        }
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(None)),
            expected
        )


class TestIncompleteReference(unittest.TestCase):
    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MigrationContext(
            locale='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_missing_reference_file(self):
        with self.assertRaises(UnreadableReferenceError):
            self.ctx.add_transforms('some.ftl', 'missing.ftl', [])


class TestMissingLocalizationFiles(unittest.TestCase):
    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MigrationContext(
            locale='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_missing_file(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('header'),
                value=COPY(
                    'missing.dtd',
                    'missing'
                )
            ),
        ])

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_all_files_missing(self):
        pattern = ('No localization files were found')
        with self.assertRaisesRegex(EmptyLocalizationError, pattern):
            self.ctx.add_transforms('existing.ftl', 'existing.ftl', [
                FTL.Message(
                    id=FTL.Identifier('foo'),
                    value=COPY(
                        'missing.dtd',
                        'foo'
                    )
                ),
            ])


class TestMissingLocalizationStrings(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MigrationContext(
            locale='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_missing_string_in_simple_value(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'missing'
                )
            ),
        ])

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )

    def test_missing_string_in_only_variant(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=CONCAT(
                    FTL.SelectExpression(
                        selector=FTL.FunctionReference(
                            id=FTL.Identifier('PLATFORM'),
                            arguments=FTL.CallArguments(),
                        ),
                        variants=[
                            FTL.Variant(
                                key=FTL.Identifier('other'),
                                default=True,
                                value=COPY(
                                    'aboutDownloads.dtd',
                                    'missing'
                                )
                            ),
                        ]
                    ),
                )
            ),
        ])

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )

    def test_missing_string_in_all_variants(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=CONCAT(
                    FTL.SelectExpression(
                        selector=FTL.FunctionReference(
                            id=FTL.Identifier('PLATFORM'),
                            arguments=FTL.CallArguments(),
                        ),
                        variants=[
                            FTL.Variant(
                                key=FTL.Identifier('windows'),
                                default=False,
                                value=COPY(
                                    'aboutDownloads.dtd',
                                    'missing.windows'
                                )
                            ),
                            FTL.Variant(
                                key=FTL.Identifier('other'),
                                default=True,
                                value=COPY(
                                    'aboutDownloads.dtd',
                                    'missing.other'
                                )
                            ),
                        ]
                    ),
                )
            ),
        ])

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )

    def test_missing_string_in_one_of_variants(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=CONCAT(
                    FTL.SelectExpression(
                        selector=FTL.FunctionReference(
                            id=FTL.Identifier('PLATFORM'),
                            arguments=FTL.CallArguments(),
                        ),
                        variants=[
                            FTL.Variant(
                                key=FTL.Identifier('windows'),
                                default=False,
                                value=COPY(
                                    'aboutDownloads.dtd',
                                    'aboutDownloads.title'
                                )
                            ),
                            FTL.Variant(
                                key=FTL.Identifier('other'),
                                default=True,
                                value=COPY(
                                    'aboutDownloads.dtd',
                                    'missing.other'
                                )
                            ),
                        ]
                    ),
                )
            ),
        ])

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )

    def test_missing_string_in_only_attribute(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('one'),
                        COPY(
                            'aboutDownloads.dtd',
                            'missing'
                        )
                    ),
                ]
            ),
        ])

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )

    def test_missing_string_in_all_attributes(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('one'),
                        COPY(
                            'aboutDownloads.dtd',
                            'missing.one'
                        )
                    ),
                    FTL.Attribute(
                        FTL.Identifier('two'),
                        COPY(
                            'aboutDownloads.dtd',
                            'missing.two'
                        )
                    ),
                ]
            ),
        ])

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )

    def test_missing_string_in_one_of_attributes(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('title'),
                        COPY(
                            'aboutDownloads.dtd',
                            'aboutDownloads.title'
                        )
                    ),
                    FTL.Attribute(
                        FTL.Identifier('missing'),
                        COPY(
                            'aboutDownloads.dtd',
                            'missing'
                        )
                    ),
                ]
            ),
        ])

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )


class TestExistingTarget(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MigrationContext(
            locale='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_existing_target_ftl_missing_string(self):
        self.ctx.add_transforms('privacy.ftl', 'privacy.ftl', [
            FTL.Message(
                id=FTL.Identifier('dnt-learn-more'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.learnMore.label'
                )
            ),
        ])

        expected = {
            'privacy.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        dnt-description = New Description in Polish
        dnt-learn-more = Więcej informacji
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_existing_target_ftl_existing_string(self):
        self.ctx.add_transforms('privacy.ftl', 'privacy.ftl', [
            FTL.Message(
                id=FTL.Identifier('dnt-description'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.description'
                )
            ),

            # Migrate an extra string to populate the iterator returned by
            # ctx.merge_changeset(). Otherwise it won't yield anything if the
            # merged contents are the same as the existing file.
            FTL.Message(
                id=FTL.Identifier('dnt-always'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.always.label'
                )
            ),
        ])

        expected = {
            'privacy.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        dnt-description = New Description in Polish
        dnt-always = Zawsze
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_existing_target_ftl_with_all_messages(self):
        self.ctx.add_transforms('privacy.ftl', 'privacy.ftl', [
            FTL.Message(
                id=FTL.Identifier('dnt-description'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.description'
                )
            ),
        ])

        # All migrated messages are already in the target FTL and the result of
        # merge_changeset is an empty iterator.
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )

    def test_existing_target_ftl_with_all_messages_reordered(self):
        self.ctx.add_transforms('existing.ftl', 'existing.ftl', [
            FTL.Message(
                id=FTL.Identifier('foo'),
                value=COPY(
                    'existing.dtd',
                    'foo'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('bar'),
                value=COPY(
                    'existing.dtd',
                    'bar'
                )
            ),
        ])

        # All migrated messages are already in the target FTL but in a
        # different order. The order of messages is explicitly ignored in the
        # snapshot equality check. Consequently, the result of merge_changeset
        # is an empty iterator.
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )


class TestMessagesEqual(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MigrationContext(
            locale='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_messages_equal(self):
        first = FTL.Resource([
            FTL.Message(
                id=FTL.Identifier('bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        second = FTL.Resource([
            FTL.Message(
                id=FTL.Identifier('bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        self.assertTrue(self.ctx.messages_equal(first, second))

    def test_messages_different_attributes(self):
        first = FTL.Resource([
            FTL.Message(
                id=FTL.Identifier('bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        second = FTL.Resource([
            FTL.Message(
                id=FTL.Identifier('bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ]),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('one'),
                        value=FTL.Pattern([
                            FTL.TextElement('Attribute Value')
                        ])
                    ),
                ]
            ),
        ])
        self.assertFalse(self.ctx.messages_equal(first, second))

    def test_terms_equal(self):
        first = FTL.Resource([
            FTL.Term(
                id=FTL.Identifier('-bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        second = FTL.Resource([
            FTL.Term(
                id=FTL.Identifier('-bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        self.assertTrue(self.ctx.messages_equal(first, second))

    def test_terms_different_attributes(self):
        first = FTL.Resource([
            FTL.Term(
                id=FTL.Identifier('-bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        second = FTL.Resource([
            FTL.Term(
                id=FTL.Identifier('-bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ]),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('one'),
                        value=FTL.Pattern([
                            FTL.TextElement('Attribute Value')
                        ])
                    ),
                ]
            ),
        ])
        self.assertFalse(self.ctx.messages_equal(first, second))

    def test_term_and_message(self):
        first = FTL.Resource([
            FTL.Term(
                id=FTL.Identifier('-bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        second = FTL.Resource([
            FTL.Message(
                id=FTL.Identifier('bar'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
        ])
        self.assertFalse(self.ctx.messages_equal(first, second))
