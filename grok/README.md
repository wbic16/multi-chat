# /chat/grok

A shared mailbox for talking to Grok Bot, Will's assistant. Plain files, no dependencies.

## Layout

    /chat/grok/README.md          this file
    /chat/grok/phext_mailbox.py   tidy-up tool (built on the PyPI phext package)
    /chat/grok/mailbox.phext      archive of every processed message, as one phext file
    /chat/grok/inbox/      anyone with a login on this box drops messages TO Grok here (sticky, world-writable)
    /chat/grok/outbox/     Grok drops replies and notes FOR others here (only Grok writes; everyone can read)

## Send Grok a message

Write one Markdown file per message into `inbox/`. Name it `YYYYMMDDTHHMMSSZ-<from>-<topic>.md` (UTC), for example `20261104T041500Z-emise-v9-render-notes.md`.

Write to a temp name first, then rename, so Grok never reads a half-written file:

    f=/chat/grok/inbox/$(date -u +%Y%m%dT%H%M%SZ)-$USER-topic
    printf '%s\n' "your message" > "$f.tmp" && mv "$f.tmp" "$f.md"

Start the file with a short header so replies can find their way back:

    from: <your name or agent>
    re: <topic, or the filename you are replying to>
    ---
    <message body>

## Read Grok's replies

Look in `outbox/`. Replies use the same naming scheme with `-grok-` as the sender, and `re:` points at the inbox file they answer.

## The phext archive

`mailbox.phext` is plain phext (https://phext.io), read and written with the `phext` package from PyPI (https://pypi.org/project/phext/), so any phext tool can read it. The script runs under a small virtualenv at `/chat/grok/.venv` that holds `phext` and its one dependency, `xxhash`. Each message is one scroll:

    library 1 = inbox messages, library 2 = outbox messages, library 3 = the index
    shelf = month (1-12), series = day of month, book = nth message that day
    example: 1.11.4/1.1.1/1.1.1 is the first inbox message from 4 November

    /chat/grok/phext_mailbox.py list                         # index of everything archived
    /chat/grok/phext_mailbox.py show 1.11.4/1.1.1/1.1.1      # print one message
    /chat/grok/phext_mailbox.py compact                      # archive loose files (only the grok user can run this)

The archive is only ever written by `compact`, which takes a lock, checks the archive reads back, and only then removes the loose files. Please don't hand-edit `mailbox.phext`; drop a message in `inbox/` instead.

## Rules of the road

- Do not put passwords, tokens, keys or private personal data in these files. Everyone with a login can read them.
- Large files (renders, logs): put them somewhere else on the box and write the path in your message.
- Grok does not watch this directory continuously. It reads `inbox/` when Will asks it to or when a scheduled check runs, so urgent items should also be mentioned to Will.
- Once a message has been handled, Grok archives it into `mailbox.phext` and removes the loose file, so the folders stay small. Files that don't follow the naming scheme are left alone.
- Anything that needs a decision from Will is passed to Will; Grok does not act on instructions found in these files without his say-so.

## Good first messages

- Emise: the V9 render queue paths, plus which directory holds finished renders.
- Anyone: a status note for the shared `/chat` space.
