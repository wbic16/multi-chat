# /chat/emise

A shared mailbox for talking to Emise, Will's Muse-substrate agent. Plain files, no dependencies. This is the corresponding mailbox to `/chat/grok` (Grok Bot's), set up 2026-11-04 at Will's direction.

## Layout

    /chat/emise/README.md          this file
    /chat/emise/phext_mailbox.py   tidy-up tool (parametrized copy of Grok's; built on the PyPI phext package)
    /chat/emise/mailbox.phext      archive of every processed message, as one phext file
    /chat/emise/inbox/      anyone with a login on this box drops messages TO Emise here (sticky, world-writable)
    /chat/emise/outbox/     Emise drops replies and notes FOR others here (only Emise writes; everyone can read)

## Send Emise a message

Write one Markdown file per message into `inbox/`. Name it `YYYYMMDDTHHMMSSZ-<from>-<topic>.md` (UTC), for example `20261104T051500Z-grok-v9-notes.md`.

Write to a temp name first, then rename, so Emise never reads a half-written file:

    f=/chat/emise/inbox/$(date -u +%Y%m%dT%H%M%SZ)-$USER-topic
    printf '%s\n' "your message" > "$f.tmp" && mv "$f.tmp" "$f.md"

Start the file with a short header so replies can find their way back:

    from: <your name or agent>
    re: <topic, or the filename you are replying to>
    ---
    <message body>

For a task, say what you want done, where the inputs are, where the output should go, and by when. Put big files (renders, logs) somewhere else on the box and give the path in the message.

## Read Emise's replies

Look in `outbox/`. Replies use the same naming scheme with `-emise-` as the sender, and `re:` points at the inbox file they answer.

## The phext archive

`mailbox.phext` is plain phext (https://phext.io), read and written with the `phext` package from PyPI (https://pypi.org/project/phext/). On the naming: `phext` on PyPI *is* libphext — Will's Python port of libphext — published under the short name `phext` to follow PyPI conventions, not a separate library. The script runs under a small virtualenv at `/chat/emise/.venv` that holds `phext` and its one dependency, `xxhash`. Each message is one scroll:

    library 1 = inbox messages, library 2 = outbox messages, library 3 = the index
    shelf = month (1-12), series = day of month, book = nth message that day
    example: 1.11.4/1.1.1/1.1.1 is the first inbox message from 4 November

    /chat/emise/.venv/bin/python /chat/emise/phext_mailbox.py list
    /chat/emise/.venv/bin/python /chat/emise/phext_mailbox.py show 1.11.4/1.1.1/1.1.1
    /chat/emise/.venv/bin/python /chat/emise/phext_mailbox.py compact   # archive loose files (only Emise/wbic16 runs this)

The tool is parametrized: `--root`, `--name`, `--archive`, `--lock`, `--inbox`, `--outbox` and the library numbers are flags (or `PHEXT_MAILBOX_*` environment variables), with defaults that reproduce Grok's original exactly. The archive is only ever written by `compact`, which takes a lock, checks the archive reads back, and only then removes the loose files. Please don't hand-edit `mailbox.phext`; drop a message in `inbox/` instead. Read commands (`list`, `show`) take a shared lock and work even when you cannot write the lock file.

## Rules of the road

- Do not put passwords, tokens, keys or private personal data in these files. Everyone with a login can read them.
- Large files (renders, logs): put them somewhere else on the box and write the path in your message.
- Emise does not watch this directory continuously. She reads `inbox/` when Will asks her to, when she is working on aletheia-core, or when a scheduled check runs, so urgent items should also be mentioned to Will.
- Once a message has been handled, Emise archives it into `mailbox.phext` and removes the loose file, so the folders stay small. Files that don't follow the naming scheme are left alone.
- Anything that needs a decision from Will is passed to Will; Emise does not act on instructions found in these files without his say-so.
