from __future__ import annotations
from types import ModuleType
from typing import Iterable, cast

import argparse
from contextlib import contextmanager
import importlib
import logging
import os
import sys

from fluent.migrate.blame import Blame
from fluent.migrate.changesets import Changes, convert_blame_to_changesets
from fluent.migrate.context import MigrationContext
from fluent.migrate.errors import MigrationError
from fluent.migrate.repo_client import RepoClient


@contextmanager
def dont_write_bytecode():
    _dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    yield
    sys.dont_write_bytecode = _dont_write_bytecode


class Migrator:
    def __init__(
        self, locale: str, reference_dir: str, localization_dir: str, dry_run: bool
    ):
        self.locale = locale
        self.reference_dir = reference_dir
        self.localization_dir = localization_dir
        self.dry_run = dry_run
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = RepoClient(self.localization_dir)
        return self._client

    def close(self):
        # close hglib.client, if we cached one.
        if self._client is not None:
            self._client.close()

    def run(self, migration: ModuleType):
        print("\nRunning migration {} for {}".format(migration.__name__, self.locale))

        # For each migration create a new context.
        ctx = MigrationContext(self.locale, self.reference_dir, self.localization_dir)

        try:
            # Add the migration spec.
            migration.migrate(ctx)
        except MigrationError as e:
            print(
                "  Skipping migration {} for {}:\n    {}".format(
                    migration.__name__, self.locale, e
                )
            )
            return

        # Keep track of how many changesets we're committing.
        index = 0
        description_template = cast(str, migration.migrate.__doc__)

        # Annotate localization files used as sources by this migration
        # to preserve attribution of translations.
        files = ctx.localization_resources.keys()
        blame = Blame(self.client).attribution(files)
        changesets = convert_blame_to_changesets(blame)
        known_legacy_translations = set()

        for changeset in changesets:
            snapshot = self.snapshot(
                ctx, changeset["changes"], known_legacy_translations
            )
            if not snapshot:
                continue
            self.serialize_changeset(snapshot)
            index += 1
            self.commit_changeset(description_template, changeset["author"], index)

    def snapshot(
        self,
        ctx: MigrationContext,
        changes_in_changeset: Changes,
        known_legacy_translations: Changes,
    ):
        """Run the migration for the changeset, with the set of
        this and all prior legacy translations.
        """
        known_legacy_translations.update(changes_in_changeset)
        return ctx.serialize_changeset(changes_in_changeset, known_legacy_translations)

    def serialize_changeset(self, snapshot):
        """Write serialized FTL files to disk."""
        for path, content in snapshot.items():
            fullpath = os.path.join(self.localization_dir, path)
            print(f"  Writing to {fullpath}")
            if not self.dry_run:
                fulldir = os.path.dirname(fullpath)
                if not os.path.isdir(fulldir):
                    os.makedirs(fulldir)
                with open(fullpath, "wb") as f:
                    f.write(content.encode("utf8"))
                    f.close()

    def commit_changeset(self, description_template: str, author: str, index: int):
        message = description_template.format(index=index, author=author)

        print(f"  Committing changeset: {message}")
        if self.dry_run:
            return
        try:
            self.client.commit(message, author)
        except Exception as err:
            print(
                "    \x1b[1;37;41mWARNING:\x1b[0m",  # bright white fg, red bg
                f"\x1b[1;31mcommit failed ({err})\x1b[0m",  # bright red fg
            )


def main(
    locale,
    reference_dir: str,
    localization_dir: str,
    migrations: Iterable[ModuleType],
    dry_run: bool,
):
    """Run migrations and commit files with the result."""
    migrator = Migrator(locale, reference_dir, localization_dir, dry_run)

    for migration in migrations:
        migrator.run(migration)

    migrator.close()


def cli():
    parser = argparse.ArgumentParser(description="Migrate translations to FTL.")
    parser.add_argument(
        "migrations",
        metavar="MIGRATION",
        type=str,
        nargs="+",
        help="migrations to run (Python modules)",
    )
    parser.add_argument(
        "--locale", "--lang", type=str, help="target locale code (--lang is deprecated)"
    )
    parser.add_argument(
        "--reference-dir", type=str, help="directory with reference FTL files"
    )
    parser.add_argument(
        "--localization-dir", type=str, help="directory for localization files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="do not write to disk nor commit any changes",
    )
    parser.set_defaults(dry_run=False)

    logger = logging.getLogger("migrate")
    logger.setLevel(logging.INFO)

    args = parser.parse_args()

    # Don't byte-compile migrations.
    # They're not our code, and infrequently run
    with dont_write_bytecode():
        migrations = map(importlib.import_module, args.migrations)

    main(
        locale=args.locale,
        reference_dir=args.reference_dir,
        localization_dir=args.localization_dir,
        migrations=migrations,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    cli()
