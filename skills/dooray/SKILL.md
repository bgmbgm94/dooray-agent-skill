---
name: dooray
description: Use Dooray's standard-user API for account, projects, posts, wiki, calendars and messenger. Read safely; request explicit approval before changes or sending messages.
---

# Dooray Agent Skill

Use `scripts/dooray.py` from this skill directory; run `python scripts/dooray.py --help` to see supported operations. Requires Python 3.10+ and a **personal** Dooray API token in `DOORAY_TOKEN`. Never print the token, copy it into messages, or check it into Git. The API base defaults to `https://api.dooray.com`.

For account/project/post/wiki/calendar/messenger endpoint details, read the corresponding `references/*.md` file only when needed. Drive operations are not enabled until independently documented public endpoints are verified. This skill only implements standard-user API operations; actual access depends on the token's permissions. It does not implement administrative API calls.

## Safe workflow

1. Start with read-only commands to identify the intended destination. Do not infer IDs from examples.
2. Before any write, show the user the target, request body, and consequences; confirm the user authorized that action.
3. Writes are **disabled by default**. To execute an authorized write, set `DOORAY_WRITE_POLICY=allow` (or `allowlist` with `DOORAY_WRITE_ALLOWLIST`), then pass `--apply`. Without both, no write request is sent.
4. Treat deletions, message sends and full-replacement updates as irreversible until proven otherwise. Re-read after a write.
5. Never send test messages, create real events, or edit remote resources just to verify the skill. Unit tests mock all network calls.

## Local invocation

```bash
python scripts/dooray.py me
python scripts/dooray.py project list
python scripts/dooray.py calendar list
```

See the root README for installation in Codex and Claude Code. This skill does not require installing a Python package.
