# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | ✅ Active          |
| 1.0.x   | ⚠️ Critical fixes only |
| < 1.0   | ❌ No longer supported |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security bugs.**

Email **security@aeo-agent.dev** (or DM [@Asiyaarab](https://github.com/Asiyaarab)
on GitHub) with:

- A description of the vulnerability and its impact
- Steps to reproduce
- The affected version

We aim to acknowledge new reports within **3 business days** and ship a fix
within **14 days** for critical issues.

## What we consider a vulnerability

- A way to bypass Scrapfly / Z.ai authentication or read other users' data
- A path-traversal, SSRF, or injection in the API
- A way to crash the scheduler or read arbitrary files on disk
- Secrets leaking through logs

## Best practices for self-hosters

- Always set a strong `SECRET_KEY` (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`)
- Put AEO Agent behind a reverse proxy (nginx / Caddy) with HTTPS
- Set `CORS_ORIGINS` to your actual frontend domain — not `*`
- Don't expose the API to the public internet without adding an auth layer
  (a future roadmap item; tracked in the [issue tracker](https://github.com/Asiyaarab/AeoAgent/issues))
- Keep your `SCRAPFLY_API_KEY` and `Z_AI_API_KEY` in `.env`, never in the repo

## Hall of fame

No reporters yet — be the first 🏆
