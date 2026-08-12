# Access & Credential Provisioning

Short pointer doc — the full procedure (with more context and history) lives in
the team's Obsidian vault: **"Cantus — Access & Credential Provisioning"**.
Ask the current maintainer or sysadmin for a link if you don't have vault access.

## The short version

- **Django admin/staff accounts**: one named account per person, created via
  `python manage.py createsuperuser` (see main [README](../README.md)) or by an
  existing admin creating a `User` with `is_staff=True` plus only the model
  permissions actually needed (e.g. `cantusdata.change_manuscript` for editing
  manuscript metadata). Default to least privilege; grant full superuser only
  when the role genuinely needs it. Never share an existing account's login.
- **Production/staging SSH access**: the requester generates their own SSH
  keypair and sends the **public** key to the sysadmin, who adds it to the
  target host(s) and grants `sudo` scoped to what the role needs (typically
  `/cantus-ultimus` operations). Never hand over a private key or an existing
  account's key.
- **Shared secrets** (`.env`: `POSTGRES_PASSWORD`, `RABBIT_PASSWORD`): these are
  infrastructure secrets, not per-person credentials. Only the sysadmin and
  active maintainers should hold them; never commit them or paste them into
  chat, issues, or docs. Rotate them if someone who held them leaves the
  project.
- **Requests**: anyone requesting access should say what role/task it's for;
  the current maintainer or sysadmin approves and makes the grant, and it gets
  logged (who, what, when, why) in the Obsidian doc above — so access can be
  reviewed or revoked later without having to reconstruct history.

See also: [Deployment runbook](DEPLOYMENT.md) for what production access is
actually used for day to day.
