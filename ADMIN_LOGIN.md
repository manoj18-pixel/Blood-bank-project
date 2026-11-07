# BloodLink Admin Login

The administrator account is created automatically by the application. No manual
registration or SQL is required.

## Live site (Vercel)

| Field | Value |
|---|---|
| Email | `admin@bloodlink.local` |
| Password | `Bl-IE0AyZGh6-6lduxB!9` |
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

## After the first login

Change the password from **Profile → Password**. The bootstrap only writes the
password when it creates the account, so your new password is kept on later
deployments. You can then remove `ADMIN_PASSWORD` from the Vercel environment
variables.

## Prefer your own credentials?

Set these in **Vercel → Project → Settings → Environment Variables**, then
redeploy:

| Key | Value |
|---|---|
| `ADMIN_EMAIL` | your admin email |
| `ADMIN_PASSWORD` | a strong password |
| `ADMIN_NAME` | optional display name |

Environment variables take priority over the built-in default.
