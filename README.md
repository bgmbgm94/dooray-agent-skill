# Dooray Agent Skill

A portable Agent Skill for Dooray personal-token workflows. One `skills/dooray/SKILL.md` drives Claude Code and Codex; Python 3.10+ and the standard library are the only runtime dependencies.

## Setup

```bash
export DOORAY_TOKEN="<your personal token>"
python skills/dooray/scripts/dooray.py --help
python skills/dooray/scripts/dooray.py me
```

Keep the token out of shell history if possible. Alternatively, store it in `~/.dooray-token` with restricted file permissions. Never commit `.env`, credentials or API responses. No API calls are made during tests.

### Claude Code

Install the repository as a local plugin, or add the `skills/dooray` directory to a Claude Code skill location. The optional `.claude-plugin/plugin.json` describes the local plugin; `SKILL.md` is under `skills/dooray/`.

### Codex

Link or copy `skills/dooray` to `$HOME/.agents/skills/dooray` (personal) or your project's `.agents/skills/dooray` directory. The skill directory contains `SKILL.md`, `scripts/`, and `references/` together; merely cloning this repository does not make it auto-discoverable in every unrelated project.

### Hermes

Install or link `skills/dooray` into your active Hermes profile's skills directory, then open a new session. The skill's `SKILL.md` references the same scripts.

## Safety

- GET requests are allowed. Every non-GET request requires **both** `--apply`/`apply=True` and an explicit `DOORAY_WRITE_POLICY=allow` or `allowlist` configuration. Default policy is `deny`.
- With `allowlist`, list permitted destination IDs in `DOORAY_WRITE_ALLOWLIST` separated by commas.
- This is a local guard, not an authorization bypass. Your Dooray personal token still needs the relevant permissions.
- Preview an intended write with the user before enabling it. Never use a real message or event as a smoke test.
- The low-level client blocks HTTP redirects rather than forwarding its Authorization header to an untrusted destination.

## Status

Unit tests mock HTTP calls and validate payloads and guard behavior. The repository does not claim live verification for all operations; check individual `references/` pages for endpoint evidence. Some supported routes or permissions may differ between Dooray organizations and API versions.

## Development

```bash
python -m unittest discover -s tests -v
```

Only public API evidence is referenced. See `THIRD-PARTY-NOTICES.md` for source links and license context.
