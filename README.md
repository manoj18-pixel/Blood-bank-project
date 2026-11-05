# BloodLink

A community blood-donor matching platform built with **HTML, CSS, JavaScript, Python Flask and SQL**. People who need blood can post a request, compatible donors nearby can offer to help, and contact details are exchanged only after an offer is accepted.

Blood is **never bought or sold** on BloodLink. There are no payments, no middlemen and no medical claims. The hospital or licensed blood bank always performs screening and cross-matching.

---

## Highlights

- Email + password accounts for donors and requesters.
- Blood-group compatibility engine (recipient → compatible donor groups).
- Donor search by blood group, city and availability, with masked phone numbers.
- Blood requests with urgency, hospital, units and needed-by time.
- Offer workflow: **offer → accept / decline / withdraw → fulfilled**.
- Contact details revealed only between the request owner and the accepted donor.
- 90-day donation cooldown with eligibility dates and automatic unavailability after donation.
- In-app notification inbox with unread counts.
- Admin console for users, requests, verification, suspension and audit logging.
- Responsive vanilla CSS design system, accessible markup and CSRF protection.
- Automated pytest suite (116 tests) covering auth, matching, eligibility, requests, offers, privacy, notifications, admin, profile, security and deployment config.

---

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Server-rendered Jinja templates, vanilla CSS and JavaScript |
| Backend | Python 3.12, Flask 3 |
| Data | SQLAlchemy ORM, SQLite for development/tests, PostgreSQL-ready |
| Auth | Flask-Login, Werkzeug password hashing, single-use tokens |
| Forms | Flask-WTF / WTForms with server-side validation |
| Security | CSRF protection, rate limiting (Flask-Limiter), CSP and security headers |
| Tests | pytest, pytest-cov, freezegun |

---

## Quick start (Windows PowerShell)

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Optional: copy environment defaults
Copy-Item .env.example .env

# 4. Create and seed the database with demo data
python seed.py --reset

# 5. Run the development server
python run.py
```

Open <http://127.0.0.1:5000>.

On macOS/Linux the virtual environment commands are `python3 -m venv .venv` and `source .venv/bin/activate`.

### Database setup without demo data

```powershell
python -m flask --app run:app init-db
python -m flask --app run:app create-admin
```

`create-admin` prompts for an email and password and creates or promotes an administrator.

---

## Demo accounts

`python seed.py --reset` creates these accounts. Every password is shown here for local testing only.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@bloodlink.local` | `Admin@12345` |
| Requester (A+, Pune) | `ravi@example.com` | `Requester@12345` |
| Requester (B+, Mumbai) | `meera@example.com` | `Requester@12345` |
| Donor (O−, Pune) | `asha@example.com` | `Donor@12345` |
| Donor (O+, Pune) | `vikram@example.com` | `Donor@12345` |
| More donors | `neha@`, `arjun@`, `sneha@`, `karan@`, `priya@`, `rohan@`, `divya@`, `aditya@`, `sameer@example.com` | `Donor@12345` |

The seed also includes open requests, a matched request with an accepted offer, a fulfilled request with a recorded donation, and example notifications.

---

## Running the tests

```powershell
# Full suite
python -m pytest -q

# With coverage
python -m pytest --cov=app --cov-report=term-missing
```

The suite uses an in-memory SQLite database, so it never touches `instance/bloodlink.db`. CSRF and rate limiting are disabled **only** in the testing configuration.

Latest local result: **116 passed**, 90% total coverage.

### What is covered

| File | Focus |
|---|---|
| `tests/test_auth.py` | Registration, login, logout, suspension, tokens, open-redirect protection |
| `tests/test_matching.py` | Compatibility matrix and donor ranking |
| `tests/test_eligibility.py` | 90-day cooldown, age, availability, requester handling |
| `tests/test_donors_search.py` | Filters, pagination, privacy, SQL-injection safety |
| `tests/test_requests.py` | Create/edit/cancel/expire/fulfil requests, XSS escaping |
| `tests/test_offers_privacy.py` | Offer lifecycle and contact-reveal rules |
| `tests/test_notifications.py` | Inbox isolation, read/unread, unread API |
| `tests/test_admin.py` | Access control, suspension, request moderation, audit log |
| `tests/test_profile.py` | Profile updates, validation, availability, password change |
| `tests/test_security.py` | Headers, cookie flags, masking, role-injection resistance |

---

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for three ready-to-use options:

- **Cloudflare Tunnel** — a temporary public link in about 5 minutes.
- **Render** — free permanent hosting with a GitHub repo and PostgreSQL.
- **Google Cloud Run** — deploy the included `Dockerfile` if you need Google hosting.
- **Vercel** — serverless deployment (PostgreSQL recommended; `index.py` and `public/static/` are included).

The repository ships with `requirements-prod.txt`, `Dockerfile`, `.dockerignore`,
`Procfile`, `render.yaml`, `index.py` and `public/`. Production runs through
Gunicorn (Render/Cloud Run) or a Vercel Python function, and `DATABASE_URL` is
normalised to the psycopg 3 driver automatically.

---

## Project structure

```
.
├── app/
│   ├── __init__.py            # App factory, filters, error pages, CLI commands
│   ├── config.py              # Development / testing / production config
│   ├── constants.py           # Blood groups, urgencies, statuses
│   ├── extensions.py          # SQLAlchemy, Login, CSRF, Limiter, Mail, Migrate
│   ├── forms.py               # WTForms with server-side validation
│   ├── models/                # User, BloodRequest, DonorResponse, Donation, ...
│   ├── services/
│   │   ├── matching.py        # Compatibility matrix, ranking, nearby requests
│   │   ├── eligibility.py     # Cooldown, age and availability rules
│   │   ├── requests.py        # Offer/accept/fulfil/cancel workflow guards
│   │   ├── notifications.py   # In-app notifications
│   │   ├── tokens.py          # Single-use verification/reset tokens
│   │   ├── mailer.py          # Optional SMTP (logs links in development)
│   │   └── audit.py           # Admin audit trail
│   ├── blueprints/            # main, auth, donors, requests, offers, profile,
│   │                          # notifications, admin
│   ├── templates/             # Jinja layouts, macros, pages, error states
│   ├── static/css/app.css     # Design system and responsive layout
│   └── static/js/app.js       # Progressive enhancements
├── tests/                     # Pytest suite
├── instance/                  # SQLite database (gitignored)
├── seed.py                    # Demo data
├── run.py                     # Development entry point
├── requirements.txt
├── requirements-prod.txt      # Gunicorn + PostgreSQL driver for hosting
├── Dockerfile                 # Production image (Cloud Run / Docker)
├── render.yaml                # Render Blueprint
├── Procfile                   # Heroku-style web process
├── index.py                   # Vercel serverless entry point
├── public/static/             # CSS/JS copied for Vercel's CDN
├── DEPLOYMENT.md              # Hosting and public-link guide
├── PROJECT_PLAN.md            # Full architecture, schema, routes and test plan
├── .env.example
└── README.md
```

---

## How the workflow works

1. **Register** with name, email, phone, blood group and city.
2. A **requester** posts a blood request with the patient, hospital, units, urgency and needed-by time.
3. **Compatible donors** see the request and press *I can help*.
4. The requester sees offers with donor city and a **masked phone number**, and accepts one.
5. On acceptance:
   - the request becomes `matched`,
   - the donor sees the requester's phone number,
   - the requester sees the donor's full phone number.
6. After the donation, the requester marks the request **fulfilled**. A donation row is created, the donor's `last_donation_date` is set, availability is switched off and the 90-day cooldown begins.
7. Declined, withdrawn, cancelled and expired paths are all handled without leaking contact details.

### Privacy rules

- Public donor JSON (`/donors/api/search`) never includes `phone`, `email` or `password_hash`.
- Donor cards and profiles show a masked phone (e.g. `92******22`).
- A request's contact number is shown to its owner and to the donor whose offer was accepted.
- Other signed-in users see a locked notice instead of the phone number.
- Suspended accounts cannot sign in and their donor profile returns 404.

### Business rules

- Blood-group compatibility follows the standard red-cell matrix in `app/services/matching.py`.
- Donors must be 18–65, available, active and outside the 90-day cooldown to offer.
- A requester cannot offer on their own request.
- One offer per donor per request (database unique constraint).
- Only open requests can be edited, cancelled or receive new offers.
- Only matched requests with an accepted offer can be marked fulfilled, once.

---

## Configuration

Copy `.env.example` to `.env` and change values as needed.

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | development placeholder | Session signing — **change in production** |
| `DATABASE_URL` | `sqlite:///instance/bloodlink.db` | SQLAlchemy connection string |
| `DONATION_COOLDOWN_DAYS` | `90` | Cooldown between donations |
| `PER_PAGE` | `20` | Pagination size |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Require verified email before donors can offer |
| `SESSION_COOKIE_SECURE` | `false` | Set to `true` behind HTTPS |
| `RATELIMIT_STORAGE_URI` | `memory://` | Use Redis in multi-process deployments |
| `MAIL_SERVER` | empty | Leave empty to log verification/reset links |

### PostgreSQL

```text
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/bloodlink
```

Install a driver such as `psycopg[binary]` and run the same `init-db`/`seed.py` commands. The models use portable SQLAlchemy types and naive UTC datetimes.

---

## Routes

| Method | Path | Description |
|---|---|---|
| GET | `/` | Landing page with live stats |
| GET | `/dashboard` | Personal dashboard |
| GET/POST | `/auth/register`, `/auth/login` | Account access |
| POST | `/auth/logout` | Sign out |
| GET/POST | `/auth/forgot`, `/auth/reset/<token>` | Password recovery |
| GET | `/donors/`, `/donors/<id>` | Donor directory and profile |
| GET | `/donors/api/search` | Safe JSON donor search |
| GET | `/requests/` | Browse/filter requests |
| GET/POST | `/requests/new`, `/requests/<id>/edit` | Create/edit request |
| GET | `/requests/<id>` | Request detail and offer panel |
| POST | `/requests/<id>/offer` | Send an offer |
| POST | `/offers/<id>/accept` \| `decline` \| `withdraw` | Manage offers |
| POST | `/requests/<id>/fulfill` | Record a donation |
| GET/POST | `/profile/`, `/profile/password` | Profile and password |
| POST | `/profile/availability` | Toggle availability |
| GET | `/notifications/` | Inbox |
| GET | `/admin/`, `/admin/users`, `/admin/requests` | Admin console |

---

## Security notes

- Passwords are hashed with Werkzeug (never stored in plain text).
- CSRF tokens protect every state-changing form.
- Login and registration are rate-limited.
- `next` redirects are validated to prevent open redirects.
- Responses set `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, a restrictive CSP and a referrer policy.
- Session cookies are `HttpOnly` and `SameSite=Lax`; enable `SESSION_COOKIE_SECURE` under HTTPS.
- Template auto-escaping prevents stored XSS.
- Admin actions are written to an audit log.

This is a learning/community project, not a certified medical system. Do not use it as the sole source of truth in an emergency.

---

## License

Free to use and adapt for learning and community projects. Add a license of your choice before publishing.
