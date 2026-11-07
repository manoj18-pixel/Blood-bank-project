# BloodLink Admin Login

The administrator account is created automatically by the application. No manual
registration or SQL is required.

## Live site (Vercel)

| Field | Value |
|---|---|
| Email | `admin@bloodlink.local` |
| Password | `adminmanoj@18` |
| Name | `BloodLink Admin` |

`index.py` calls `ensure_admin_from_env()` on cold start. If `ADMIN_EMAIL` and
`ADMIN_PASSWORD` are not set, `ensure_default_admin()` creates the account above.

## Local development

The seeded demo database already contains the admin account:

| Field | Value |
|---|---|
| Email | `admin@bloodlink.local` |
| Password | `Admin@12345` |

Re-create the demo data any time with:

```powershell
.\.venv\Scripts\python.exe seed.py
```

## About changing the password

The bootstrap applies the configured password on every cold start, so the admin
password is always the one in `ADMIN_PASSWORD` (or the built-in
`adminmanoj@18` when the variable is absent). To use your own private password,
set `ADMIN_PASSWORD` in Vercel and redeploy.

## Prefer your own credentials?

Set these in **Vercel → Project → Settings → Environment Variables**, then
redeploy:

| Key | Value |
|---|---|
| `ADMIN_EMAIL` | your admin email |
| `ADMIN_PASSWORD` | a strong password |
| `ADMIN_NAME` | optional display name |

Environment variables take priority over the built-in default.
