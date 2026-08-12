# Deploying to Staging and Production

Short pointer doc — the full runbook (SSH aliases, troubleshooting, known
issues) lives in the team's Obsidian vault: **"Cantus — Deploying to Staging
and Production"**. Ask the current maintainer or sysadmin for a link if you
don't have vault access. See [ACCESS.md](ACCESS.md) first if you don't yet
have SSH/sudo access to the target server.

## The short version

1. `ssh` into the target host using your personal SSH config alias, then
   confirm you're on the right box with `hostname` — **the production
   hostname is misleadingly named and does not look like a production
   server; do not assume it's safe to experiment on because of its name.**
2. `sudo -i && cd /cantus-ultimus` (the repo there is owned by `root`; all
   git/docker operations must run as root).
3. `git status && git diff` — check for server-specific local modifications
   (e.g. `nginx/nginx.conf`) before pulling, and `git stash` them if present.
4. `git fetch && git pull`, then `git submodule status` — flag any `-` or `+`
   prefixed submodule to the sysadmin before continuing.
5. `git stash pop` to restore local modifications; resolve conflicts if any.
6. Restart: `docker compose restart` for backend-only changes. For frontend
   changes (`cantus-min.js` / Diva.js), rebuild first:
   `docker compose build nginx && docker compose up -d nginx`.
7. Verify: `docker ps -a` — all containers should be `Up`. If any are
   `Exited`, check `docker logs <container-name>`.

## Known rough edges (flagged for the incoming sysadmin)

- **Production hostname is misleading** (looks like a dev/test box). This has
  already caused at least one near-miss where someone assumed it was safe to
  treat as non-production.
- **Docker log rotation was never configured.** A large, unrotated container
  log is a known cause of `docker compose build` failing with
  "no space left on device." Worth setting up rotation proactively rather
  than firefighting the next time disk fills up. If diagnosing an existing
  large log, check its date range (`head -1`/`tail -1` on the log file)
  before truncating anything, and don't truncate without checking with the
  sysadmin — the log may still be needed for debugging.
- **Kubernetes migration in progress** (per recent commit history) may
  partially supersede this Docker Compose workflow. Treat this runbook as
  current-but-transitional, not final.
- Remote is HTTPS; pushing directly from the server isn't the intended
  workflow — merge to `main` on GitHub, then pull it down here.
