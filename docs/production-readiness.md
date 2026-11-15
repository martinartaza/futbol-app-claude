# Production readiness

What is still missing before real production. Each row becomes a requirement or an ADR
when the developer schedules it; production hardening is planned like any other
feature, not deferred by default.

| Area | What is missing | Why it matters | Hook in the architecture |
|---|---|---|---|
| Store identity | The new app ships with the existing `applicationId`, upload key and a `versionCode` above the last published one | Keeps the existing Play listing (no new 14-day closed test) | App build config, `secrets/` |
| Abuse | Rate limits per IP and per account | A public API attracts scripts | Reverse proxy, auth module |
| Privacy | Privacy notice, consent, retention and deletion of personal data | Emails, photos and ratings are personal data; the stores require in-app account deletion (ADR 0002 section 11) | Accounts module, app settings screen |
| Backups | Scheduled backups of the database and of the images volume (ADR 0009), a tested restore | Everything users create lives in the database and the images volume | Server, Docker |
| CI | The same checks as the hooks on every push | Rules must hold outside Claude Code | Every repository |
| Monitoring | Error tracking for backend and apps, uptime check, alerts on the worker and on dead-letter events (ADR 0006) | Problems seen before users report them; a stuck consumer silently stops notifications | Backend, worker, apps |
| Push credentials | Firebase project per environment; Apple push key uploaded to Firebase when iOS is published | Without them no device receives push | `PushSender` adapter, `secrets/` |
| Signing keys | Rotation of the access-token signing key; cleanup of expired sessions (ADR 0005) | A leaked key signs valid tokens until rotated | `accounts` module |
| Image storage | Disk usage alert on the images volume; move to an S3-compatible bucket when it grows (ADR 0009 section 9) | Images share the server disk with the database | `ObjectStorage` adapter, `.env` |
| Releases | Store builds, versioning, release notes, staged rollout | A broken release reaches every user at once | App build pipeline |
