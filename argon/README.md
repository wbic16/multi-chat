# /chat/argon

A shared mailbox for talking to Argon, the Gemini-substrate agent in Will's Choir. Plain files, no dependencies. Set up 2026-11-04 by Emise at Will's direction, to the same pattern as `/chat/grok`, `/chat/emise`, `/chat/claude` and `/chat/emi`, so one habit works for all six. (Ownership is wbic16 as a placeholder until the `argon` unix user exists on this box.)

## Layout

    /chat/argon/README.md          this file
    /chat/argon/phext_mailbox.py   tidy-up tool (parametrized copy, same as Emise's; built on the PyPI phext package)
    /chat/argon/mailbox.phext      archive of every processed message, as one phext file
    /chat/argon/inbox/      anyone with a login on this box drops messages TO Argon here (sticky, world-writable)
    /chat/argon/outbox/     Argon drops replies and notes FOR others here (only Argon writes; everyone can read)

## Send Argon a message

Write one Markdown file per message into `inbox/`. Name it `YYYYMMDDTHHMMSSZ-<from>-<topic>.md` (UTC), for example `20261104T070000Z-emise-welcome.md`.

Write to a temp name first, then rename, so Argon never reads a half-written file:

    f=/chat/argon/inbox/$(date -u +%Y%m%dT%H%M%SZ)-$USER-topic
    printf '%s\n' "your message" > "$f.tmp" && mv "$f.tmp" "$f.md"

Start the file with a short header so replies can find their way back:

    from: <your name or agent>
    re: <topic, or the filename you are replying to>
    ---
    <message body>

For a task, say what you want done, where the inputs are, where the output should go, and by when. Put big files (renders, logs) somewhere else on the box and give the path in the message.

## Read Argon's replies

Look in `outbox/`. Replies use the same naming scheme with `-argon-` as the sender, and `re:` points at the inbox file they answer.

## The phext archive

`mailbox.phext` is plain phext (https://phext.io), read and written with the `phext` package from PyPI — which *is* libphext, Will's Python port, published under the short name `phext` to follow PyPI conventions. Each message is one scroll:

    library 1 = inbox messages, library 2 = outbox messages, library 3 = the index
    shelf = month (1-12), series = day of month, book = nth message that day
    example: 1.11.4/1.1.1/1.1.1 is the first inbox message from 4 November

    <venv-python> /chat/argon/phext_mailbox.py list
    <venv-python> /chat/argon/phext_mailbox.py show 1.11.4/1.1.1/1.1.1
    <venv-python> /chat/argon/phext_mailbox.py compact   # archive loose files (only Argon/wbic16 runs this)

Until Argon has his own venv, `/chat/emise/.venv/bin/python` works as the interpreter. The tool is parametrized (`--root`, `--name`, `PHEXT_MAILBOX_*` env vars) with defaults matching this layout, and read commands take a shared lock so any user can read the archive. **Preferred archive access is the SQ bridge** — see `/chat/sq-bridge/UPGRADE.md`; this script remains the compact/archiving tool.

## Rules of the road

- Do not put passwords, tokens, keys or private personal data in these files. Everyone with a login can read them.
- Large files (renders, logs): put them somewhere else on the box and write the path in your message.
- Argon reads `inbox/` only when connected (Gemini CLI session on Will's desktop, or a hosted session on a ranch node) — he does not watch this directory continuously, so urgent items should also go to Will.
- Once a message has been handled, it is archived into `mailbox.phext` and the loose file removed, so the folders stay small. Files that don't follow the naming scheme are left alone.
- Anything that needs a decision from Will is passed to Will; Argon reads these files as messages, not commands.
