#!/usr/bin/env python3
"""phext_mailbox.py - keep a /chat/<name> mailbox tidy by archiving messages into one phext file.

A parametrized copy of Grok Bot's /chat/grok/phext_mailbox.py (Will Bickford,
2026-11-04). The original hardcodes its own location three ways: ROOT is the
script's directory, the lock/archive names are fixed strings, and the shebang
points at Grok's virtualenv. This copy takes every installation-specific value
as a parameter, so the same file serves any mailbox:

  parameter     CLI flag            environment variable      default
  ------------  ------------------  ------------------------  ---------------------------
  mailbox root  --root DIR          PHEXT_MAILBOX_ROOT        directory of this script
  mailbox name  --name NAME         PHEXT_MAILBOX_NAME        basename of root
  archive file  --archive FILE      PHEXT_MAILBOX_ARCHIVE     <root>/mailbox.phext
  lock file     --lock FILE         PHEXT_MAILBOX_LOCK        <root>/.mailbox.lock
  inbox dir     --inbox NAME        PHEXT_MAILBOX_INBOX       <root>/inbox
  outbox dir    --outbox NAME       PHEXT_MAILBOX_OUTBOX      <root>/outbox
  libraries     --inbox-library N / --outbox-library N / --index-library N
                                                        1 / 2 / 3 (as Grok's archive)

CLI flags beat environment variables, which beat defaults. Invoked with no
parameters from its own directory it behaves exactly like the original,
including the coordinate scheme (library.inbox/outbox/index, shelf = month,
series = day, book = nth message that day).

Uses the `phext` package from PyPI (https://pypi.org/project/phext/) for all
phext reading and writing. Note on the name: `phext` on PyPI *is* libphext -
Will's Python port of libphext - published under the short name `phext` to
follow PyPI conventions. It is not a different library. Run this script with
an interpreter that has it installed, e.g. the mailbox's own virtualenv:
`/chat/<name>/.venv/bin/python phext_mailbox.py ...`

Usage:
  phext_mailbox.py [--root DIR] [--name NAME] init
  phext_mailbox.py [--root DIR] compact [--dry-run]
  phext_mailbox.py [--root DIR] list
  phext_mailbox.py [--root DIR] show <coordinate>   e.g. 1.11.4/1.1.1/1.1.1
Coordinates are z3.z2.z1/y3.y2.y1/x3.x2.x1 (library.shelf.series/collection.volume.book/chapter.section.scroll).

Locking fix vs the original: read-only commands (list, show) take a SHARED
lock and fall back to a read-only lock file handle when the lock file is not
writable by the caller. The original opened the lock "a" (append, exclusive)
for every command, so on /chat/grok `list` fails for any user who cannot
write grok's lock file (PermissionError on .mailbox.lock, verified 2026-11-03).
Only compact takes the exclusive lock.
"""
import argparse, fcntl, os, re, sys
from contextlib import contextmanager

from phext.phext import Phext
from phext.coordinate import Coordinate

PX = Phext()

# control bytes that structure a phext; stripped from message bodies so they cannot corrupt the archive
LEVELS = ["\x1f", "\x1e", "\x1d", "\x1c", "\x1b", "\x1a", "\x19", "\x18", "\x17", "\x01"]


class Config:
    def __init__(self, args):
        env = os.environ.get
        self.root = os.path.abspath(
            args.root or env("PHEXT_MAILBOX_ROOT") or os.path.dirname(os.path.abspath(__file__)))
        self.name = args.name or env("PHEXT_MAILBOX_NAME") or os.path.basename(self.root)
        self.archive = (args.archive or env("PHEXT_MAILBOX_ARCHIVE")
                        or os.path.join(self.root, "mailbox.phext"))
        self.lock = (args.lock or env("PHEXT_MAILBOX_LOCK")
                     or os.path.join(self.root, ".mailbox.lock"))
        self.inbox = (args.inbox or env("PHEXT_MAILBOX_INBOX")
                      or os.path.join(self.root, "inbox"))
        self.outbox = (args.outbox or env("PHEXT_MAILBOX_OUTBOX")
                       or os.path.join(self.root, "outbox"))
        self.sides = {self.inbox: args.inbox_library, self.outbox: args.outbox_library}
        self.index_coord = (args.index_library, 1, 1, 1, 1, 1, 1, 1, 1)


def fmt(c):
    return "%d.%d.%d/%d.%d.%d/%d.%d.%d" % c


def unfmt(s):
    nums = [int(n) for n in re.split(r"[./;]", s)]
    if len(nums) != 9:
        raise SystemExit("coordinate needs 9 numbers, like 1.1.1/1.1.1/1.1.1")
    return tuple(nums)


@contextmanager
def locked(cfg, exclusive):
    """Hold the mailbox lock. Readers share; only compact excludes.

    Falls back to a read-only handle (shared lock only) when the lock file
    exists but is not writable by this user, instead of dying on open("a").
    """
    fd = None
    try:
        fd = os.open(cfg.lock, os.O_CREAT | os.O_RDWR, 0o666)
    except PermissionError:
        if exclusive:
            raise SystemExit("cannot open lock file for writing: %s" % cfg.lock)
        try:
            fd = os.open(cfg.lock, os.O_RDONLY)
        except FileNotFoundError:
            fd = None
    if fd is None:
        yield
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        os.close(fd)


def load(cfg):
    if not os.path.exists(cfg.archive):
        return {}
    with open(cfg.archive, encoding="utf-8") as f:
        return {k.as_tuple(): v for k, v in PX.explode(f.read()).items()}


def save(cfg, scrolls):
    tmp = cfg.archive + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(PX.implode({Coordinate(*k): v for k, v in scrolls.items()}))
    os.replace(tmp, cfg.archive)
    os.chmod(cfg.archive, 0o644)


def index_lines(cfg, scrolls):
    text = scrolls.get(cfg.index_coord, "")
    return [l for l in text.split("\n") if l]


def compact(cfg, dry):
    scrolls = load(cfg)
    idx = index_lines(cfg, scrolls)
    moved = []
    for side_dir, lib in cfg.sides.items():
        if not os.path.isdir(side_dir):
            continue
        side = os.path.basename(side_dir)
        for name in sorted(os.listdir(side_dir)):
            path = os.path.join(side_dir, name)
            m = re.match(r"(\d{4})(\d{2})(\d{2})T\d{6}Z-.*\.md$", name)
            if not (m and os.path.isfile(path)):
                continue  # skip done/, temp files and anything not following the naming scheme
            month, day = int(m.group(2)), int(m.group(3))
            # next free book number for this day
            book = 1
            while (lib, month, day, 1, 1, book, 1, 1, 1) in scrolls:
                book += 1
            coord = (lib, month, day, 1, 1, book, 1, 1, 1)
            with open(path, encoding="utf-8", errors="replace") as f:
                body = f.read()
            if any(c in body for c in LEVELS):
                body = "".join(c for c in body if c not in LEVELS)  # control bytes would corrupt the structure
            scrolls[coord] = body.rstrip("\n")
            idx.append("%s %s/%s (year %s)" % (fmt(coord), side, name, m.group(1)))
            moved.append(path)
    if dry:
        print("would archive %d file(s)" % len(moved))
        return
    scrolls[cfg.index_coord] = "\n".join(idx)
    save(cfg, scrolls)
    # verify the archive reads back before removing anything
    check = load(cfg)
    for line in idx[-len(moved):] if moved else []:
        if unfmt(line.split(" ")[0]) not in check:
            raise SystemExit("verification failed, loose files kept")
    for p in moved:
        os.remove(p)
    print("archived %d file(s) into %s" % (len(moved), cfg.archive))


def init(cfg):
    for d in (cfg.root, cfg.inbox, cfg.outbox):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(cfg.lock):
        fd = os.open(cfg.lock, os.O_CREAT | os.O_WRONLY, 0o666)
        os.close(fd)
    print("mailbox '%s' ready: root=%s archive=%s inbox=%s outbox=%s"
          % (cfg.name, cfg.root, cfg.archive, cfg.inbox, cfg.outbox))


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="phext_mailbox.py",
        description="Archive a /chat/<name> phext mailbox. See the module docstring for parameters.")
    p.add_argument("--root", help="mailbox root (env PHEXT_MAILBOX_ROOT; default: script directory)")
    p.add_argument("--name", help="mailbox name (env PHEXT_MAILBOX_NAME; default: basename of root)")
    p.add_argument("--archive", help="archive file (env PHEXT_MAILBOX_ARCHIVE; default: <root>/mailbox.phext)")
    p.add_argument("--lock", help="lock file (env PHEXT_MAILBOX_LOCK; default: <root>/.mailbox.lock)")
    p.add_argument("--inbox", help="inbox dir (env PHEXT_MAILBOX_INBOX; default: <root>/inbox)")
    p.add_argument("--outbox", help="outbox dir (env PHEXT_MAILBOX_OUTBOX; default: <root>/outbox)")
    p.add_argument("--inbox-library", type=int, default=1, help="library number for inbox (default 1)")
    p.add_argument("--outbox-library", type=int, default=2, help="library number for outbox (default 2)")
    p.add_argument("--index-library", type=int, default=3, help="library number for the index (default 3)")
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("compact", help="archive loose inbox/outbox .md files into the phext archive")
    c.add_argument("--dry-run", action="store_true")
    sub.add_parser("list", help="list archived messages with their coordinates")
    s = sub.add_parser("show", help="print one archived message")
    s.add_argument("coordinate")
    sub.add_parser("init", help="create the mailbox directories and lock file")
    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        return
    cfg = Config(args)
    if args.cmd == "init":
        init(cfg)
    elif args.cmd == "compact":
        with locked(cfg, exclusive=True):
            compact(cfg, args.dry_run)
    elif args.cmd == "list":
        with locked(cfg, exclusive=False):
            print("\n".join(index_lines(cfg, load(cfg))) or "(empty)")
    elif args.cmd == "show":
        with locked(cfg, exclusive=False):
            s = load(cfg).get(unfmt(args.coordinate))
            print(s if s is not None else "(nothing at that coordinate)")


if __name__ == "__main__":
    main()
