# Deploying BloodLink (hosting + sharing a link)

Right now the app runs at `http://127.0.0.1:5000`, which only works on **your own
PC**. To let other people open it, the app has to run on a machine that is
reachable from the internet.

There are three practical options:

| Option | Time | Link stays alive | Best for |
|---|---|---|---|
| **A. Cloudflare Tunnel** | 5 minutes | Only while your PC + server run | Demo to friends right now |
| **B. Render (free)** | 20–30 minutes | Yes, even when your PC is off | A real, permanent link |
| **C. Google Cloud Run** | 30–60 minutes | Yes | "Host on Google", needs billing |
| **D. Vercel** | 10 minutes | Yes | You already use Vercel; **requires PostgreSQL** |

The repo now includes everything these hosts need:

- `requirements-prod.txt` — Gunicorn + PostgreSQL driver
- `Dockerfile` — production image (Cloud Run / any Docker host)
- `render.yaml` — Render Blueprint
- `Procfile` — Heroku-style start command
- `vercel.json` + `api/index.py` — Vercel serverless entry point

---

## Option A — Fastest: temporary public link (Cloudflare Tunnel)

No account, no GitHub, no code changes. Your PC must stay on and the Flask
server must keep running.

### 1. Install cloudflared (one time)

```powershell
winget install --id Cloudflare.cloudflared
```

Close the terminal and open a new one so the `cloudflared` command is found.

### 2. Start the app

In one terminal:

```powershell
cd "C:\Users\Manoj\OneDrive\Documents\Default Project"
.\.venv\Scripts\python.exe run.py
```

### 3. Start the tunnel

In a **second** terminal:

```powershell
cd "C:\Users\Manoj\OneDrive\Documents\Default Project"
.\share.ps1
```

Or run cloudflared directly:

```powershell
cloudflared tunnel --url http://127.0.0.1:5000
```

It prints something like:

```text
https://random-words-here.trycloudflare.com
```

Copy that `https://...` link and send it on WhatsApp. Anyone can open it while
both terminals are running.

> Notes
> - The link changes every time you restart the tunnel.
> - Your PC must stay on. Closing the terminal kills the link.
> - This uses Flask's development server. Fine for a demo, not for real users.

---

## Option B — Permanent free hosting on Render

Render gives you a URL like `https://bloodlink-xxxx.onrender.com` that stays
online even when your PC is off. It needs a GitHub repository.

### 1. Push the project to GitHub

Create an **empty** repository at <https://github.com/new> (do not add a README),
then run:

```powershell
cd "C:\Users\Manoj\OneDrive\Documents\Default Project"
git init
git add .
git commit -m "BloodLink ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/bloodlink.git
git push -u origin main
```

`.venv/`, `instance/` and `.env` are ignored by `.gitignore`, so your local
database and secrets are **not** uploaded.

### 2. (Recommended) Create a free PostgreSQL database

Render's free web service has an ephemeral disk: with SQLite, data disappears on
every deploy/restart. For data that survives, use a free PostgreSQL:

- <https://neon.tech> — create a project, copy the `postgresql://...` connection
  string. The app automatically rewrites it to `postgresql+psycopg://`.

### 3. Create the Render service

1. Sign up at <https://render.com> with GitHub.
2. **New** → **Blueprint** → select your `bloodlink` repository.
3. Render reads `render.yaml` automatically.
4. If you created a Neon database, open the service → **Environment** → add:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | your Neon connection string |

5. Click **Apply / Deploy**.

The start command runs `flask --app run:app init-db` first, so tables are created
automatically.

### 4. Create your admin account

Render dashboard → your service → **Shell**:

```bash
flask --app run:app create-admin
```

Enter an email, a strong password and a name. Then sign in on the public URL.

### 5. Share the link

Render shows the URL at the top of the service page:

```text
https://bloodlink-xxxx.onrender.com
```

Send that link to anyone. The free instance sleeps after ~15 minutes of
inactivity; the first visit may take 30–60 seconds to wake up.

> To use SQLite instead of PostgreSQL (demo only), skip step 2. Everything works,
> but accounts and requests reset on every deploy.

---

## Option C — Google Cloud Run ("Google la host")

Cloud Run is the correct Google product for a Flask app. Firebase Hosting cannot
run Python/Flask by itself. Cloud Run requires a **billing account** (there is a
free tier, but a card must be on file).

### 1. Install the Google Cloud CLI

```powershell
winget install --id Google.CloudSDK
```

Open a new terminal, then:

```powershell
gcloud auth login
gcloud config set project YOUR-PROJECT-ID
```

In the Google Cloud Console, enable billing and the **Cloud Run**, **Cloud
Build** and **Artifact Registry** APIs.

### 2. Deploy straight from this folder

```powershell
cd "C:\Users\Manoj\OneDrive\Documents\Default Project"
gcloud run deploy bloodlink --source . --region asia-south1 --allow-unauthenticated
```

Google builds the included `Dockerfile` and prints a public URL like:

```text
https://bloodlink-xxxxxxxxx-as.a.run.app
```

### 3. Set environment variables

```powershell
gcloud run services update bloodlink --region asia-south1 --update-env-vars FLASK_ENV=production,SECRET_KEY=REPLACE-WITH-A-LONG-RANDOM-STRING,DATABASE_URL=YOUR-POSTGRES-URL
```

Cloud Run containers have no permanent disk, so **use PostgreSQL** (Neon or Cloud
SQL). Never rely on SQLite there.

### 4. Create the admin

Easiest: register a normal account through the website, then promote it in your
PostgreSQL SQL editor:

```sql
UPDATE users SET role = 'admin', email_verified = true WHERE email = 'you@example.com';
```

Then sign in again.

---

## Option D — Vercel (serverless, PostgreSQL required)

Vercel cannot run Flask from the repository root and cannot write SQLite files.
The repository includes the required glue:

- `api/index.py` — WSGI entry point; creates the schema on cold start
- `vercel.json` — rewrites every route to the function
- `psycopg[binary]` in `requirements.txt`

**A PostgreSQL database is mandatory.** Use Neon (free): create a project and
copy the `postgresql://...` connection string.

### 1. Import the project

1. <https://vercel.com/new> → import `manoj18-pixel/Blood-bank-project`.
2. Framework Preset: **Other**.
3. Build Command: leave empty.
4. Output Directory: leave empty.
5. Install Command: `pip install -r requirements.txt`.

### 2. Environment variables

Add these before deploying (or in Project → Settings → Environment Variables):

| Key | Value |
|---|---|
| `DATABASE_URL` | Neon `postgresql://...` string |
| `SECRET_KEY` | long random string |
| `FLASK_ENV` | `production` |

Click **Deploy**. Vercel gives a URL like
`https://blood-bank-project.vercel.app`.

### 3. Create the admin

Vercel has no shell. Register a normal account on the site, then promote it in
the Neon SQL editor:

```sql
UPDATE users SET role = 'admin', email_verified = true WHERE email = 'you@example.com';
```

### Vercel limits to know

- Functions are short-lived; `Flask-Limiter` counters are per instance.
- Every cold start runs `db.create_all()`, which is idempotent.
- SQLite is not usable; data only persists in PostgreSQL.
- The free Hobby plan is for demos, not production traffic.

---

## Before you share the link (important)

| Check | Why |
|---|---|
| `SECRET_KEY` is long and random | Otherwise sessions can be forged |
| `FLASK_ENV=production` | Enables secure cookies and disables debug |
| `DATABASE_URL` points to PostgreSQL | SQLite is wiped on restarts |
| You created your own admin | Never share the demo `Admin@12345` password |
| `REQUIRE_EMAIL_VERIFICATION=true` | Optional: stops fake signups |
| `MAIL_SERVER` configured | Optional: real verification/reset emails |

Demo accounts from `seed.py` are for local testing only. Do **not** run
`python seed.py` on a public server.

### Environment variables reference

| Variable | Example | Purpose |
|---|---|---|
| `FLASK_ENV` | `production` | Selects `ProductionConfig` |
| `SECRET_KEY` | 64 random characters | Session signing |
| `DATABASE_URL` | `postgresql://...` | Persistent database |
| `REQUIRE_EMAIL_VERIFICATION` | `true` | Require verified email before offering |
| `SESSION_COOKIE_SECURE` | `true` | HTTPS-only cookies (already true in production) |
| `MAIL_SERVER` | `smtp.gmail.com` | Real email delivery |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | SMTP credentials | Email login |
| `RATELIMIT_STORAGE_URI` | `memory://` | Use Redis if you run many instances |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `cloudflared` not recognised | Close and reopen the terminal after `winget install` |
| Render build fails | Check logs; Python must be 3.12 (`PYTHON_VERSION=3.12.7`) |
| `ModuleNotFoundError: psycopg` | Build command must be `pip install -r requirements-prod.txt` |
| Tables missing / `no such table` | Start command must run `flask --app run:app init-db` first |
| 500 error after deploy | Check `SECRET_KEY` and `DATABASE_URL`; read the service logs |
| Free Render app is slow on first visit | Normal: the free instance sleeps when idle |
| `postgres://` driver error | Already handled; the app rewrites it to `postgresql+psycopg://` |

---

## Which one should I pick?

- **Just show a friend today** → Option A (Cloudflare Tunnel).
- **A real link for a college project / portfolio** → Option B (Render + Neon).
- **You specifically need Google** → Option C (Cloud Run + Neon).
- **You already deployed on Vercel** → Option D, and make sure `DATABASE_URL` is set.
