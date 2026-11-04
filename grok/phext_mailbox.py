#!/chat/grok/.venv/bin/python
"""phext_mailbox.py - keep /chat/grok tidy by archiving messages into one phext file.

Uses the phext package from PyPI (https://pypi.org/project/phext/) for all phext reading and writing. Usage:
  phext_mailbox.py compact [--dry-run]   archive inbox/*.md and outbox/*.md into mailbox.phext, then remove them
  phext_mailbox.py list                  list archived messages with their coordinates
  phext_mailbox.py show <coordinate>     print one archived message, e.g. 1.1.1/1.1.1/1.1.1
Coordinates are z3.z2.z1/y3.y2.y1/x3.x2.x1 (library.shelf.series/collection.volume.book/chapter.section.scroll).
"""
import fcntl, os, re, sys

from phext.phext import Phext
from phext.coordinate import Coordinate

PX = Phext()

ROOT = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(ROOT, "mailbox.phext")
LOCK = os.path.join(ROOT, ".mailbox.lock")
# control bytes that structure a phext; stripped from message bodies so they cannot corrupt the archive
LEVELS = ["\x1f", "\x1e", "\x1d", "\x1c", "\x1b", "\x1a", "\x19", "\x18", "\x17", "\x01"]
DIRECTION = {"inbox": 1, "outbox": 2}  # library number
INDEX_COORD = (3, 1, 1, 1, 1, 1, 1, 1, 1)  # library 3 holds the index scroll


def fmt(c):
    return "%d.%d.%d/%d.%d.%d/%d.%d.%d" % c


def unfmt(s):
    nums = [int(n) for n in re.split(r"[./;]", s)]
    if len(nums) != 9:
        raise SystemExit("coordinate needs 9 numbers, like 1.1.1/1.1.1/1.1.1")
    return tuple(nums)


def load():
    if not os.path.exists(ARCHIVE):
        return {}
    with open(ARCHIVE, encoding="utf-8") as f:
        return {k.as_tuple(): v for k, v in PX.explode(f.read()).items()}


def save(scrolls):
    tmp = ARCHIVE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(PX.implode({Coordinate(*k): v for k, v in scrolls.items()}))
    os.replace(tmp, ARCHIVE)
    os.chmod(ARCHIVE, 0o644)


def index_lines(scrolls):
    text = scrolls.get(INDEX_COORD, "")
    return [l for l in text.split("\n") if l]


def compact(dry):
    scrolls = load()
    idx = index_lines(scrolls)
    moved = []
    for side, lib in DIRECTION.items():
        d = os.path.join(ROOT, side)
        for name in sorted(os.listdir(d)):
            path = os.path.join(d, name)
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
    scrolls[INDEX_COORD] = "\n".join(idx)
    save(scrolls)
    # verify the archive reads back before removing anything
    check = load()
    for line in idx[-len(moved):] if moved else []:
        if unfmt(line.split(" ")[0]) not in check:
            raise SystemExit("verification failed, loose files kept")
    for p in moved:
        os.remove(p)
    print("archived %d file(s) into %s" % (len(moved), ARCHIVE))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    with open(LOCK, "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        if cmd == "compact":
            compact("--dry-run" in sys.argv)
        elif cmd == "list":
            print("\n".join(index_lines(load())) or "(empty)")
        elif cmd == "show" and len(sys.argv) > 2:
            s = load().get(unfmt(sys.argv[2]))
            print(s if s is not None else "(nothing at that coordinate)")
        else:
            print(__doc__)


if __name__ == "__main__":
    main()
