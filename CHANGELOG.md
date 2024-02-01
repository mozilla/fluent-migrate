# Changelog

## fluent.migrate 0.13.0 (Feb 1, 2024)

  - Add RepoClient as wrapper that auto-detects and supports both git & hg ([#6](https://github.com/mozilla/fluent-migrate/pull/6))
  - Add some type hinting
  - Drop support for Python 3.7, add 3.11 and 3.12

## fluent.migrate 0.12.0 (May 16, 2023)

  - Trim plural variants in fluent.migrate `PLURALS()` ([Bug 1794286](https://bugzilla.mozilla.org/show_bug.cgi?1794286))
  - Update dependencies to compare-locales 9.0.1 & fluent.syntax 0.19.0
  - Add support for Python 3.8, 3.9 & 3.10
  - Drop Python 2 support
  - Drop Windows support
  - Drop dependency on six
  - Update contact details, including new [repo URL](https://github.com/mozilla/fluent-migrate)

## fluent.migrate 0.11 (March 12, 2021)

  - Change default behaviour for normalize_printf for .properties files

## fluent.migrate 0.10 (September 18, 2020)

  - Update to fluent.syntax 0.18.
  - Update to compare-locales 0.8.1.

## fluent.migrate 0.9 (May 13, 2020)

*Breaking Changes*

  - [Bug 1616056](https://bugzilla.mozilla.org/show_bug.cgi?id=1616056) - trim by default for `LegacySource` transforms, but not inside `CONCAT`.

Other Changes:

  - [Bug 1626976](https://bugzilla.mozilla.org/show_bug.cgi?id=1626976) - transforms can raise `fluent.migrate.errors.SkipTransform` to not transform a string, even if it exists in a localization.

## fluent.migrate 0.8.1 (February 26, 2020)

  - Follow up to bilingual files, let migration code enforce serializing non-localized content.

## fluent.migrate 0.8 (February 26, 2020)

  - Support multi-locale repositories as targets.
  - Better recipe validation.
  - When migrating from bilingual files, check that messages are translated.
  - Base class `transforms.TransformPattern` to modify Fluent patterns during migrations.

## fluent.migrate 0.7.1 (November 13, 2019)

  - Make dependency on `python-hglib` optional.

## fluent.syntax 0.7.0 (November 13, 2019)

  - `MigrationContext` is a public API now.
  - Split off `InternalContext` for non-public functionality and
  internal APIs.
  - Support `migrate-l10n` w/out `--reference-dir` to create vanilla
  Fluent files from migration recipes.
  - First release to upload to PyPI.

This is just an excerpt of the [full changelog](https://hg.mozilla.org/l10n/fluent-migration/changelog?rev=0.6.4::0.7.0&revcount=80).

## fluent 0.6.4 (March 1, 2018)

  - use compare-locales for plurals ordering ([bug 1415844](https://bugzilla.mozilla.org/show_bug.cgi?id=1415844))
  - create transforms when all dependencies have been met up to a changeset

## fluent 0.6.3 (February 13, 2018)

  - Fix merge code to handle Terms properly

## fluent 0.6.2 (February 8, 2018)

  - Require compare-locales to run and test fluent.migrate. (#47)

## fluent 0.6.1 (February 6, 2018)

Various fixes to `fluent.migrate` for [bug 1424682][].

[bug 1424682]: https://bugzilla.mozilla.org/show_bug.cgi?id=1424682

  - Accept `Patterns` and `PatternElements` in `REPLACE`. (#41)

    `REPLACE` can now use `Patterns`, `PatternElements` and `Expressions` as
    replacement values. This makes `REPLACE` accept the same Transforms as
    `CONCAT`.

  - Never migrate partial translations. (#44)

    Partial translations may break the AST because they produce
    `TextElements` with `None` values. For now, we explicitly skip any
    transforms which depend on at least one missing legacy string to avoid
    serialization errors.

  - Warn about unknown FTL entries in transforms. (#40)
  - Fix how files are passed to `hg annotate`. (#39)

## fluent 0.6.0 (January 31, 2018)

  - Implement Fluent Syntax 0.5.

    - Add support for terms.
    - Add support for `#`, `##` and `###` comments.
    - Remove support for tags.
    - Add support for `=` after the identifier in message and term
      defintions.
    - Forbid newlines in string expressions.
    - Allow trailing comma in call expression argument lists.

    In fluent-syntax 0.6.x the new Syntax 0.5 is supported alongside the old
    Syntax 0.4. This should make migrations easier.

    `FluentParser` will correctly parse Syntax 0.4 comments (prefixed with
    `//`), sections and message definitions without the `=` after the
    identifier. The one exception are tags which are no longer supported.
    Please use attributed defined on terms instead.

    `FluentSerializer` always serializes using the new Syntax 0.5.

  - Expose `FluentSerializer.serializeExpression`. (#134)

  - Fix Bug 1428000 - Migrate: only annotate affected files (#34)


## fluent 0.4.4 (November 29, 2017)

  - Bug 1411943 - Fix Blame for Mercurial 4.3+ (#23)
  - Bug 1412808 - Remove the LITERAL helper. (#25)
  - Bug 1321279 - Read target FTL files before migrations. (#24)

    The reference file for the transforms must now be passed as the second
    argument to add_transforms.

  - Bug 1318960 - Migrate files only when their messages change (#26)
  - Bug 1366298 - Skip SelectExpression in PLURALS for one plural category (#27)
  - Bug 1321290 - Migrate HTML entities to Unicode characters (#28)
  - Bug 1420225 - Read legacy files when scanning for Sources in transforms (#30)

    MergeContext.maybe_add_localization is now automatically called
    interally when the context encounters a transforms which is a subclass of
    Source.


## fluent 0.4.3 (October 9, 2017)

  - No changes affecting migration in this release of python-fluent


## fluent 0.4.2 (September 11, 2017)

  - Add an intermediate Placeable node for Expressions within Patterns.

    This allows storing more precise information about the whitespace around
    the placeable's braces.

    See https://github.com/projectfluent/fluent/pull/52.

## fluent 0.4.1 (June 27, 2017)

  - No changes affecting migration in this release of python-fluent

## fluent 0.4.0 (June 13, 2017)

  - This is the first release to be listed in the CHANGELOG.
