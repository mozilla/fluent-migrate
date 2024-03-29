from __future__ import annotations
from typing import Set, Tuple, TypedDict

import time

from .blame import BlameResult

Changes = Set[Tuple[str, str]]


class Changeset(TypedDict):
    author: str
    first_commit: float
    changes: Changes


def by_first_commit(item: Changeset):
    """Order two changesets by their first commit date."""
    return item["first_commit"]


def convert_blame_to_changesets(blame_json: BlameResult) -> list[Changeset]:
    """Convert a blame dict into a list of changesets.

    The blame information in `blame_json` should be a dict of the following
    structure:

        {
            'authors': [
                'A.N. Author <author@example.com>',
            ],
            'blame': {
                'path/one': {
                    'key1': [0, 1346095921.0],
                },
            }
        }

    It will be transformed into a list of changesets which can be fed into
    `InternalContext.serialize_changeset`:

        [
            {
                'author': 'A.N. Author <author@example.com>',
                'first_commit': 1346095921.0,
                'changes': {
                    ('path/one', 'key1'),
                }
            },
        ]

    """
    now = time.time()
    changesets: list[Changeset] = [
        {"author": author, "first_commit": now, "changes": set()}
        for author in blame_json["authors"]
    ]

    for path, keys_info in blame_json["blame"].items():
        for key, (author_index, timestamp) in keys_info.items():
            changeset = changesets[author_index]
            changeset["changes"].add((path, key))
            if timestamp < changeset["first_commit"]:
                changeset["first_commit"] = timestamp

    return sorted(changesets, key=by_first_commit)
