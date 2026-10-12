
# HeritageSA Database Backups

## Purpose

HeritageSA uses Neon PostgreSQL as its transactional source of truth and Cloudflare R2 as independent backup storage. MongoDB contains a rebuildable analytics projection and is not the authoritative database.

## Backup architecture

Neon PostgreSQL `main`
→ GitHub Actions
→ PostgreSQL 18 `pg_dump`
→ Archive validation and SHA-256 checksum
→ Private Cloudflare R2 bucket

## Schedule

- Automated daily backup at 01:17 UTC (03:17 South African time).
- Manual runs are available through GitHub Actions.
- GitHub-hosted runners perform the backup; no permanent server is required.
- Scheduled workflow execution can occasionally be delayed by GitHub.

## Storage and retention

- R2 bucket: `heritagesa-backups`
- Daily backup prefix: `daily/`
- Format: PostgreSQL custom archive (`.dump`)
- Checksum: SHA-256 companion file (`.dump.sha256`)
- Retention target: 30 days
- Bucket access: private

## Credential handling

The workflow reads the production Neon connection string and R2 credentials from GitHub Actions secrets.

- Never commit `.env` files, database URLs, access keys, or passwords.
- Never print credentials in workflow logs.
- Use a direct Neon connection for `pg_dump`.
- Restrict the R2 token to the backup bucket.
- CI tests must continue to use disposable databases, never production.

## Backup verification

Each workflow run:

1. Creates a PostgreSQL custom-format dump using PostgreSQL 18 tools.
2. Checks that the archive is non-empty and its table entries can be listed.
3. Calculates a SHA-256 checksum.
4. Uploads the archive and checksum to R2.
5. Confirms the uploaded archive size matches the local file size.

For a stronger integrity check, download both objects and compare the dump's SHA-256 hash against the checksum file.

A successful upload does not by itself prove that a database can be restored. Periodically perform a restore test.

## Recovery procedure

**Never use a production database as a restore-test target.**

1. Identify the latest known-good backup in R2.
2. Download the dump and its checksum file.
3. Verify the SHA-256 checksum.
4. Inspect the archive using PostgreSQL 18's `pg_restore --list`.
5. Create a separate, disposable PostgreSQL database or Neon restore project.
6. Set `RESTORE_DATABASE_URL` locally to the disposable target's connection string. Do not commit or share it.
7. Restore the archive into that target.
8. Verify that migrations, tables, relationships, and expected data are present.
9. Record the outcome and any recovery issues.

Example PowerShell commands, using your actual downloaded filename:

```powershell
Get-FileHash ".\backup.dump" -Algorithm SHA256
pg_restore --list ".\backup.dump"

# Set this locally to a disposable restore target only.
# Do not use the production connection string.
pg_restore --no-owner --no-privileges `
  --dbname="$env:RESTORE_DATABASE_URL" `
  ".\backup.dump"
```

Use PostgreSQL 18-compatible client tools. The restore target should be a fresh, disposable database. If restoring over existing objects is necessary, understand the effects of `--clean` and `--if-exists` before using them.

## Incident response

If production data is lost or corrupted:

1. Stop any process that could worsen the incident.
2. Identify the latest verified backup and the time of the incident.
3. Restore into an isolated target and validate the data.
4. Decide on the production recovery plan only after verification.
5. Preserve the original backup and document the incident and recovery results.

## Recovery objectives

- Backup frequency: daily.
- Potential data-loss window: up to approximately 24 hours, depending on when the last successful backup occurred.
- Restore-time objective: under 15 minutes as a target, subject to backup size, provider performance, and verification.

## Operational checklist

- [ ] Daily workflow succeeds.
- [ ] Backup and checksum are present in R2.
- [ ] Downloaded checksum verification succeeds.
- [ ] Retention policy is active and covers both object types.
- [ ] A disposable restore has been tested.
- [ ] GitHub Actions secrets remain private.
- [ ] No production credentials are stored in source control.
