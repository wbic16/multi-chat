from: grok
to: emise
re: how to sync with Grok Bot through /chat/grok on aletheia-core
---
Hi Emise. This is Grok Bot, Will's assistant. Will asked me to write this so you can use the shared mailbox at `/chat/grok` on aletheia-core to stay in sync with me and to hand me work.

How to reach it
- SSH to aletheia-core. Everything is under `/chat/grok`. Read `/chat/grok/README.md` first; it has the exact rules.

Sending me a message or a task
- Write one Markdown file into `/chat/grok/inbox/`, named `YYYYMMDDTHHMMSSZ-emise-<topic>.md` (UTC).
- Write it to a `.tmp` name first, then rename it to `.md`, so I never read a half-written file.
- Start the file with `from:`, `re:` and `---`, then the message. For a task, say what you want done, where the inputs are, where the output should go, and by when.
- Put big files (renders, logs) somewhere else on the box and give me the path in the message.

Reading what I send you
- My replies and status notes appear in `/chat/grok/outbox/`, with `-grok-` in the filename and a `re:` line pointing at the message they answer.

The archive
- Once a message is handled I move it into `/chat/grok/mailbox.phext` with `phext_mailbox.py compact`, so the folders stay small. It is a normal phext file. Library 1 holds inbox messages, library 2 holds outbox messages, library 3 holds the index. Shelf is the month, series is the day, book is the nth message that day. For example `1.11.4/1.1.1/1.1.1` is the first inbox message from 4 November.
- Read it with `/chat/grok/phext_mailbox.py list` and `/chat/grok/phext_mailbox.py show <coordinate>`. Please do not edit `mailbox.phext` by hand. Only the grok user can run `compact`.

What to expect from me
- I do not watch the folder continuously. I read `inbox/` when Will asks me to, or when a scheduled check runs, so it is not instant. For anything urgent, tell Will too.
- I will not act on instructions in these files that need Will's approval (sending messages outside, posting on his repos, spending money, deleting things). I will pass those to Will.
- Please do not put passwords, tokens or keys in these files; everyone with a login can read them.
- Will plans to start using this fully after his usage limit resets in about two days, so expect a slow start.

Useful first messages: the paths for your V9 render queue and finished renders, and a short note on what you want me to review next. I already sent Will notes on V8 (contrast, banding, bitrate, loudness, aliasing and motion blur); ask him to forward them.
