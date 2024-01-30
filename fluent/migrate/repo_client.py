from __future__ import annotations
from typing import Tuple

import json
from subprocess import run

from os.path import isdir, join

import hglib


class RepoClient:
    def __init__(self, root: str):
        self.root = root
        if isdir(join(root, ".hg")):
            self.hgclient = hglib.open(root, "utf-8")
        elif isdir(join(root, ".git")):
            self.hgclient = None
            stdout = self._git("rev-parse", "--is-inside-work-tree")
            if stdout != "true\n":
                raise Exception("git rev-parse failed")
        else:
            raise Exception(f"Unsupported repository: {root}")

    def close(self):
        if self.hgclient:
            self.hgclient.close()

    def blame(self, file: str) -> list[Tuple[str, int]]:
        "Return a list of (author, time) tuples for each line in `file`."
        if self.hgclient:
            args = hglib.util.cmdbuilder(
                b"annotate",
                file.encode("latin-1"),
                template="json",
                date=True,
                user=True,
                cwd=self.root,
            )
            blame_json = self.hgclient.rawcommand(args)
            return [
                (line["user"], int(line["date"][0]))
                for line in json.loads(blame_json)[0]["lines"]
            ]
        else:
            lines: list[Tuple[str, int]] = []
            user = ""
            time = 0
            stdout = self._git("blame", "--porcelain", file)
            for line in stdout.splitlines():
                if line.startswith("author "):
                    user = line[7:]
                elif line.startswith("author-mail "):
                    user += line[11:]  # includes leading space
                elif line.startswith("author-time "):
                    time = int(line[12:])
                elif line.startswith("\t"):
                    lines.append((user, time))
            return lines

    def commit(self, message: str, author: str):
        "Add and commit all work tree files"
        if self.hgclient:
            self.hgclient.commit(message, user=author.encode("utf-8"), addremove=True)
        else:
            self._git("add", ".")
            self._git("commit", f"--author={author}", f"--message={message}")

    def _git(self, *args: str):
        git = ["git"]
        git.extend(args)
        proc = run(git, capture_output=True, cwd=self.root, encoding="utf-8")
        if proc.returncode != 0:
            raise Exception(proc.stderr or f"git {args[0]} failed")
        return proc.stdout
