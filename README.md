L10n Migration Tools
====================

`migrate-l10n.py` is a CLI script which uses the `fluent.migrate` module under
the hood to run migrations on existing translations.

Installation
------------

The tool is best installed by installing the package. As we haven't published the tool on pypi yet, the best way to do so is to run the following command in a virtualenv from your local clone:

    pip install .

Usage
-----

Migrations consist of _recipes_, which are applied to a _localization repository_, based on _template files_.
You can find recipes for Firefox in `mozilla-central/python/l10n/fluent_migrations/`,
the reference repository is [gecko-strings](https://hg.mozilla.org/l10n/gecko-strings/) or _quarantine_.
You apply those migrations to l10n repositories in [l10n-central](https://hg.mozilla.org/l10n-central/), or to `gecko-strings` for testing.

The migrations are run as python modules, so you need to have their file location in `PYTHONPATH`.

An example would look like

    $ migrate-l10n --lang it --reference-dir gecko-strings --localization-dir l10n-central/it bug_1451992_preferences_sitedata bug_1451992_preferences_translation

Contact
-------

 - mailing list: https://lists.mozilla.org/listinfo/tools-l10n
 - IRC channel: [irc://irc.mozilla.org/l20n](irc://irc.mozilla.org/l20n)
 - bugzilla: [Open Bugs](https://bugzilla.mozilla.org/buglist.cgi?component=Fluent%20Migration&product=Localization%20Infrastructure%20and%20Tools&bug_status=__open__) - [New Bug](https://bugzilla.mozilla.org/enter_bug.cgi?product=Localization%20Infrastructure%20and%20Tools&component=Fluent%20Migration)
