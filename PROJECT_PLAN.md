# BloodLink — Blood Bank Community Platform

### Full-Stack Project Plan (v1.0)

| Item | Detail |
|---|---|
| Project name | **BloodLink** — community blood donor & request network |
| Document | Project plan, architecture, database design, test plan |
| Stack | HTML5, CSS3, Vanilla JavaScript, Python 3.12 + Flask 3, SQL (SQLite dev / PostgreSQL prod) |
| Prepared | 2026-11-05 |
| Status | Ready for build |
| Author | Project team |

---

## 1. Executive Summary

BloodLink is a **community-driven blood availability platform**. A person who needs blood posts a request; registered donors with a compatible blood group and a nearby location are matched to that request. The requester can then contact a willing donor — but **contact details are only revealed after the donor explicitly accepts**, protecting both parties.

The product borrows **e-commerce mechanics** (catalog → listing → order → fulfilment → reputation) but is **not a paid marketplace**. Blood is never bought or sold. There is no checkout, no price, and no payment. The "commerce" layer is matching, requests, accept/decline, fulfilment tracking, notifications, and trust/reputation.

### The one-sentence goal

> Reduce the time to find a compatible, available, nearby blood donor from hours of phone calls to under 5 minutes.

---

## 2. Problem Statement

| Pain point | Current reality | BloodLink response |
|---|---|---|
| Finding donors is slow | WhatsApp forwards, phone chains, hospital notice boards | Searchable donor registry filtered by group + city + availability |
| Donor lists go stale | People donate once, stay on lists forever | 90-day eligibility cooldown, self-service availability toggle |
| Privacy risk | Phone numbers are broadcast in public groups | Contact revealed only after donor accepts an offer |
| No accountability | Unknown whether a lead is genuine | Verified email, request lifecycle, donation history, admin moderation |
| Requests are untraceable | No status, no follow-up | Request statuses: open → matched → fulfilled / cancelled / expired |

---

## 3. Goals & Non-Goals

### 3.1 Goals (MVP)

1. Email + password registration and secure authentication.
2. Donor profile with blood group, city/area, availability, and last donation date.
3. Blood request creation with hospital, urgency, units, and needed-by time.
4. Donor search with **blood-group compatibility**, city, and availability filters.
5. **Offer → accept → contact reveal** flow between donor and requester.
6. In-app notifications for offers, accepts, and request updates.
7. Donation recording with automatic 90-day cooldown and eligibility status.
8. Admin moderation (users, requests, reports) and basic platform stats.
9. Responsive, accessible UI.
10. Automated test suite with ≥ 70% coverage and a documented manual E2E pass.

### 3.2 Non-Goals (explicitly out of scope for v1)

- Selling blood, payments, or any monetary transaction.
- Medical diagnosis, cross-matching, or clinical eligibility certification.
- Real-time chat (contact happens off-platform by phone/WhatsApp after consent).
- Native mobile apps (responsive web only; PWA is Phase 2).
- HIPAA/GDPR certification (design follows privacy best practices, but no formal audit).
- Live hospital inventory integration (Phase 3).

---

## 4. Users & Personas

| Persona | Needs | Key screens |
|---|---|---|
| **Requester (Ravi)** — needs blood for a relative | Post request fast, see compatible available donors, get a confirmed helper | New request, request detail, matched donors |
| **Donor (Asha)** — willing to donate | Control availability, see nearby compatible requests, protect phone number | Dashboard, request feed, offer form |
| **Both (dual role)** — most users | One account, two modes | Profile, donation history, notifications |
| **Admin (hospital/NGO staff)** | Remove fake requests, suspend abusers, see activity | Admin console |

**Rule:** every account can be both a requester and a donor. `is_donor` is a profile flag, not a separate account type.

---

## 5. Scope & Feature Specification

MoSCoW priority: **M** = must, **S** = should, **C** = could.

### 5.1 Accounts & Authentication

| ID | Feature | Priority | Notes |
|---|---|---|---|
| F-01 | Register with full name, email, password | M | Email unique, case-insensitive |
| F-02 | Password hashing | M | Werkzeug `generate_password_hash` (scrypt/PBKDF2) or bcrypt |
| F-03 | Login / logout with session | M | Flask-Login, `HttpOnly` + `SameSite=Lax` cookies |
| F-04 | Email verification | S | Token link; unverified users can browse but not offer |
| F-05 | Forgot / reset password | S | Single-use token, 60-min expiry |
| F-06 | Change password | S | Requires current password |
| F-07 | Rate limiting on auth | M | 5 failed logins / 15 min per IP + email |
| F-08 | CSRF protection on all forms | M | Flask-WTF |
| F-09 | Account suspension | M | Admin only; suspended users cannot log in |
| F-10 | Delete my account | C | Soft delete + anonymise PII |

### 5.2 Donor Profile

| ID | Feature | Priority |
|---|---|---|
| F-11 | Blood group (8 values, validated) | M |
| F-12 | Phone number (private by default) | M |
| F-13 | City, area, pincode; optional lat/lng | M |
| F-14 | Availability toggle ("Available to donate") | M |
| F-15 | Last donation date + auto eligibility calculation | M |
| F-16 | Date of birth (must be 18–65 to donate) | S |
| F-17 | Donation count, last donation, badges | S |
| F-18 | Public donor card with masked contact (`98******10`) | M |
| F-19 | Reputation: response rate, completed donations | C |

### 5.3 Blood Requests

| ID | Feature | Priority |
|---|---|---|
| F-20 | Create request: patient, group, units, hospital, city, urgency, needed-by, contact | M |
| F-21 | Edit / cancel own request | M |
| F-22 | Status lifecycle with guarded transitions | M |
| F-23 | Auto-expire past `needed_by` | M |
| F-24 | Urgency levels: normal / urgent / critical | S |
| F-25 | Matched-donor list ranked by compatibility, distance, availability, recency | M |
| F-26 | Requester sees offers with donor public profile (no phone yet) | M |
| F-27 | Mark request fulfilled (records donation) | M |
| F-28 | Share request via copyable public link (no PII) | C |

### 5.4 Matching & Contact

| ID | Feature | Priority |
|---|---|---|
| F-29 | Blood compatibility engine (recipient ← donor) | M |
| F-30 | Filter by city / pincode / radius | M |
| F-31 | Donor sends offer with optional message | M |
| F-32 | Requester accepts or declines an offer | M |
| F-33 | Contact revealed to both sides **only after accept** | M |
| F-34 | Donor can withdraw an offer | M |
| F-35 | Prevent self-offer and duplicate offers | M |
| F-36 | Notify both parties at every step | M |
| F-37 | Optional map view of nearby donors | C |

### 5.5 Donations, Notifications, Admin

| ID | Feature | Priority |
|---|---|---|
| F-38 | Record donation (donor, date, hospital, units, linked request) | M |
| F-39 | 90-day cooldown; donor marked unavailable until eligible | M |
| F-40 | Notification list + unread badge | M |
| F-41 | Email notification (offer received / accepted) | C |
| F-42 | Admin: user list, suspend/reactivate, verify | M |
| F-43 | Admin: request list, remove/close | M |
| F-44 | Admin: dashboard counts (users, open requests, donations, fulfilment rate) | M |
| F-45 | Admin audit log | S |
| F-46 | Report a request/user | S |

### 5.6 Explicit constraints

- **No price, cart, checkout, or payment fields anywhere.** Blood must remain free.
- Do not expose phone/email in HTML, JSON, or logs unless the viewer is an authorised party after acceptance.
- Do not show full address of a donor; city/area only.
- Show a medical disclaimer on the request form and request detail page.

---

## 6. Core User Flows

### 6.1 Registration → availability

```
Landing → Register (email, password, name)
        → Verify email (optional in MVP)
        → Complete profile (blood group, phone, city, DOB, last donation)
        → Available to donate = ON
        → Dashboard
```

### 6.2 Requester flow

```
Dashboard → "Need blood"
        → Fill request (patient, group, units, hospital, needed-by, urgency)
        → System computes compatible donor groups
        → Ranked donor list (city + availability + eligibility)
        → Donor offers appear on request page
        → Accept one offer → phone numbers revealed
        → Coordinate → Mark fulfilled → Record donation
```

### 6.3 Donor flow

```
Dashboard → "Requests near me" (compatible + city)
        → Open request → Read hospital/urgency
        → "I can help" (+ message)
        → Requester accepts
        → Contact revealed → Donate → Request marked fulfilled
        → last_donation_date updated → availability OFF for 90 days
```

### 6.4 Offer state machine

```
                 accept            donation recorded
  offered ───────────────► accepted ─────────────────► donated
     │  │                     │
     │  └── decline ─────────► declined
     └──── withdraw ─────────► withdrawn

  Request: open ──► matched ──► fulfilled
              └──► cancelled
              └──► expired (needed_by passed)
```

Guard rules:
- Only the request owner may accept/decline.
- Only the offering donor may withdraw.
- `accepted` requires request status `open`; accepting moves request to `matched`.
- Marking fulfilled requires an `accepted`/`donated` response and creates a donation record.
- Transitions are validated server-side, never trusted from the client.

---

## 7. Blood Compatibility Rules

A recipient can receive only from compatible donor groups:

| Recipient | Can receive from |
|---|---|
| O− | O− |
| O+ | O−, O+ |
| A− | O−, A− |
| A+ | O−, O+, A−, A+ |
| B− | O−, B− |
| B+ | O−, O+, B−, B+ |
| AB− | O−, A−, B−, AB− |
| AB+ | O−, O+, A−, A+, B−, B+, AB−, AB+ |

Derived rules:
- **O−** is the universal donor (can give to all).
- **AB+** is the universal recipient.
- Store the matrix in `app/services/matching.py` as a single immutable dict — one source of truth, covered by tests.

### 7.1 Donor eligibility (`app/services/eligibility.py`)

A donor is **eligible now** if all are true:

1. `is_available = 1` and `is_donor = 1`
2. Account `status = 'active'` and email verified (if verification enabled)
3. Age 18–65 at the time of the request
4. `last_donation_date` is `NULL` or ≥ **90 days** ago (configurable `DONATION_COOLDOWN_DAYS`)
5. Not already accepted for another open request (soft rule, warn only)

Return a reason code (`available`, `cooldown`, `unavailable`, `underage`, `suspended`) so the UI can explain *why* a donor is hidden or greyed out. Never compute eligibility in JavaScript only.

---

## 8. Matching Algorithm

```python
def rank_donors(request, donors):
    score = 0
    score += 40 if donor.blood_group == request.blood_group else 25  # exact vs compatible
    score += max(0, 30 - distance_km * 3)                            # ≤10 km
    score += 20 if donor.is_available else 0
    score += 10 if donor.email_verified else 0
    score += 5 if donor.last_donation_date is None else 0
    score += min(10, donor.completed_donations * 2)
    return score
```

Pipeline:

```
1. compatible_groups = COMPATIBILITY[request.blood_group]
2. SQL filter: blood_group IN (...) AND city = :city AND is_donor = 1 AND status = 'active'
3. Python filter: eligibility (cooldown, age, availability)
4. Rank by score, tie-break by distance then last active
5. Paginate (20 per page), return public donor cards only
```

If fewer than 3 local matches, broaden to `pincode prefix` then `state/region` and label results **"Nearby"** vs **"Other cities"**.

---

## 9. Tech Stack & Dependencies

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Required |
| Web framework | Flask 3.x (app factory + blueprints) | Required, lightweight |
| Templating | Jinja2 | Server-rendered HTML, fast to build |
| ORM / DB access | Flask-SQLAlchemy 3 + Alembic (Flask-Migrate) | Parameterised queries, migrations |
| Database | SQLite (dev/test), PostgreSQL (prod) | SQL as required, zero-setup dev |
| Auth | Flask-Login + Werkzeug password hashing | Session auth for server-rendered app |
| Forms / CSRF | Flask-WTF + WTForms | Validation + CSRF in one place |
| Rate limiting | Flask-Limiter | Brute-force protection |
| Email | Flask-Mail (SMTP) | Verification + notification emails |
| Frontend | HTML5, CSS3 (custom + Bootstrap 5 optional), Vanilla JS (`fetch`) | Required |
| Tests | pytest, pytest-cov, freezegun | Unit + integration |
| Quality | ruff, black, bandit, pip-audit | Lint, format, security |
| CI | GitHub Actions | Automated test on push |

`requirements.txt` (starting point):

```txt
Flask>=3.0,<4.0
Flask-SQLAlchemy>=3.1,<4.0
Flask-Login>=0.6,<1.0
Flask-WTF>=1.2,<2.0
Flask-Migrate>=4.0,<5.0
Flask-Limiter>=3.7,<4.0
Flask-Mail>=0.9,<1.0
email-validator>=2.1,<3.0
python-dotenv>=1.0,<2.0
psycopg[binary]>=3.2,<4.0
pytest>=8.2,<9.0
pytest-cov>=5.0,<7.0
freezegun>=1.5,<2.0
ruff>=0.5
bandit>=1.7
```

---

## 10. System Architecture

```
┌──────────────────────────── Browser ────────────────────────────┐
│  HTML/Jinja pages   CSS design system   Vanilla JS (fetch/AJAX)  │
│  live donor filters · availability toggle · notification badge   │
└───────────────┬─────────────────────────────────────────────────┘
                │ HTTPS (cookies: HttpOnly, Secure, SameSite=Lax)
┌───────────────▼─────────────────────────────────────────────────┐
│                        Flask application                        │
│  ┌──────────── Blueprints ────────────┐  ┌──── Services ──────┐  │
│  │ auth · main · donors · requests    │  │ matching           │  │
│  │ offers · profile · notifications   │  │ eligibility        │  │
│  │ admin                              │  │ notifications      │  │
│  └────────────────┬───────────────────┘  │ security/audit     │  │
│                   │                      └─────────┬──────────┘  │
│  ┌────────────────▼────────────┐   ┌───────────────▼─────────┐  │
│  │ WTForms validation + CSRF   │   │ SQLAlchemy models       │  │
│  │ Flask-Login session         │   │ transactions + indexes  │  │
│  │ Flask-Limiter               │   └───────────────┬─────────┘  │
│  └─────────────────────────────┘                   │            │
└────────────────────────────────────────────────────┼────────────┘
                                                     │ SQL
                              ┌──────────────────────▼─────────────┐
                              │ SQLite (dev/test) / PostgreSQL     │
                              │ users · requests · responses ·     │
                              │ donations · notifications · tokens │
                              └────────────────────────────────────┘
                              Optional: SMTP for email, cron/CLI
                              job for expiry + reminder emails
```

Request lifecycle (server side):

```
Route → Form.validate() → Service (business rules) → Model/DB → Flash + redirect
                     ↘ 400 with field errors            ↘ notification row
```

---

## 11. Data Model

### 11.1 Entity relationship diagram

```
users 1 ───< blood_requests        (requester_id)
users 1 ───< donor_responses       (donor_id)
blood_requests 1 ───< donor_responses (request_id)
users 1 ───< donations             (donor_id)
blood_requests 1 ───< donations    (request_id, nullable)
users 1 ───< notifications         (user_id)
users 1 ───< auth_tokens           (user_id)
users 1 ───< audit_logs            (actor_id)
```

### 11.2 SQL schema (SQLite dialect; PostgreSQL-compatible with minor type changes)

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name          TEXT    NOT NULL CHECK (length(full_name) BETWEEN 2 AND 80),
  email              TEXT    NOT NULL UNIQUE COLLATE NOCASE,
  password_hash      TEXT    NOT NULL,
  phone              TEXT    NOT NULL,
  blood_group        TEXT    NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  date_of_birth      TEXT,
  gender             TEXT    CHECK (gender IN ('male','female','other') OR gender IS NULL),
  city               TEXT    NOT NULL,
  area               TEXT,
  pincode            TEXT,
  latitude           REAL,
  longitude          REAL,
  is_donor           INTEGER NOT NULL DEFAULT 1 CHECK (is_donor IN (0,1)),
  is_available       INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0,1)),
  last_donation_date TEXT,
  email_verified     INTEGER NOT NULL DEFAULT 0 CHECK (email_verified IN (0,1)),
  role               TEXT    NOT NULL DEFAULT 'user'  CHECK (role IN ('user','admin')),
  status             TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleted')),
  created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_users_match ON users (blood_group, city, is_available, status);
CREATE INDEX idx_users_city  ON users (city);

CREATE TABLE blood_requests (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  requester_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  patient_name   TEXT    NOT NULL,
  patient_age    INTEGER CHECK (patient_age BETWEEN 0 AND 120),
  blood_group    TEXT    NOT NULL CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
  units_needed   INTEGER NOT NULL DEFAULT 1 CHECK (units_needed BETWEEN 1 AND 10),
  hospital_name  TEXT    NOT NULL,
  address        TEXT    NOT NULL,
  city           TEXT    NOT NULL,
  pincode        TEXT,
  latitude       REAL,
  longitude      REAL,
  urgency        TEXT    NOT NULL DEFAULT 'normal' CHECK (urgency IN ('normal','urgent','critical')),
  needed_by      TEXT    NOT NULL,
  contact_phone  TEXT    NOT NULL,
  notes          TEXT,
  status         TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open','matched','fulfilled','cancelled','expired')),
  created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at     TEXT    NOT NULL DEFAULT (datetime('now')),
  fulfilled_at   TEXT
);
CREATE INDEX idx_requests_search ON blood_requests (status, blood_group, city, needed_by);
CREATE INDEX idx_requests_owner  ON blood_requests (requester_id, created_at);

CREATE TABLE donor_responses (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id  INTEGER NOT NULL REFERENCES blood_requests(id) ON DELETE CASCADE,
  donor_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status      TEXT    NOT NULL DEFAULT 'offered'
              CHECK (status IN ('offered','accepted','declined','withdrawn','donated')),
  message     TEXT,
  created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
  UNIQUE (request_id, donor_id)
);
CREATE INDEX idx_responses_request ON donor_responses (request_id, status);
CREATE INDEX idx_responses_donor   ON donor_responses (donor_id, created_at);

CREATE TABLE donations (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  donor_id      INTEGER NOT NULL REFERENCES users(id),
  request_id    INTEGER REFERENCES blood_requests(id) ON DELETE SET NULL,
  hospital_name TEXT,
  donated_on    TEXT    NOT NULL,
  units         INTEGER NOT NULL DEFAULT 1 CHECK (units BETWEEN 1 AND 4),
  notes         TEXT,
  verified_by   INTEGER REFERENCES users(id),
  created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_donations_donor ON donations (donor_id, donated_on);

CREATE TABLE notifications (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type       TEXT    NOT NULL,           -- offer_received, offer_accepted, request_matched, ...
  title      TEXT    NOT NULL,
  body       TEXT    NOT NULL,
  link       TEXT,
  is_read    INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0,1)),
  created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_notifications_user ON notifications (user_id, is_read, created_at);

CREATE TABLE auth_tokens (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT    NOT NULL UNIQUE,
  purpose    TEXT    NOT NULL CHECK (purpose IN ('verify_email','reset_password')),
  expires_at TEXT    NOT NULL,
  used_at    TEXT,
  created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE audit_logs (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
  action     TEXT    NOT NULL,
  target     TEXT,
  meta       TEXT,
  created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

**Storage notes**
- Dates as ISO-8601 `YYYY-MM-DD` / `YYYY-MM-DDTHH:MM:SS` strings in SQLite; use `DATE`/`TIMESTAMP` in PostgreSQL.
- Never store plaintext phone/email beyond what the product needs; encrypt nothing at rest in v1 (SQLite file permissions) but add field-level encryption in Phase 2 if deploying publicly.
- `users.email` is `COLLATE NOCASE` so `A@x.com` and `a@x.com` cannot both register.
- Use `db.session` transactions; wrap accept-offer + notification + status change in one transaction.

---

## 12. Routes & API Reference

Legend: **Auth** = logged-in, **Owner** = resource owner, **Admin** = role check, **Public** = no login.

### 12.1 HTML pages

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/` | Public | Landing: hero, search widget, live stats, how it works |
| GET/POST | `/auth/register` | Public | Create account |
| GET/POST | `/auth/login` | Public | Sign in |
| POST | `/auth/logout` | Auth | Sign out (CSRF-protected) |
| GET | `/auth/verify/<token>` | Public | Verify email |
| GET/POST | `/auth/forgot` | Public | Request reset link |
| GET/POST | `/auth/reset/<token>` | Public | Set new password |
| GET | `/dashboard` | Auth | Role-aware summary + quick actions |
| GET | `/donors` | Auth | Search donors |
| GET | `/donors/<id>` | Auth | Donor public card (masked contact) |
| GET | `/requests` | Auth | Browse open requests |
| GET/POST | `/requests/new` | Auth | Create request |
| GET | `/requests/<id>` | Auth | Detail + matched donors + offers |
| GET/POST | `/requests/<id>/edit` | Owner | Edit open request |
| POST | `/requests/<id>/cancel` | Owner | Cancel |
| POST | `/requests/<id>/fulfill` | Owner | Mark fulfilled + record donation |
| POST | `/requests/<id>/offer` | Auth donor | Send offer |
| POST | `/offers/<id>/accept` | Owner | Accept offer → reveal contact |
| POST | `/offers/<id>/decline` | Owner | Decline |
| POST | `/offers/<id>/withdraw` | Donor | Withdraw |
| GET | `/profile` | Auth | View/edit own profile |
| POST | `/profile` | Auth | Update profile |
| POST | `/profile/availability` | Auth | Toggle availability |
| POST | `/profile/password` | Auth | Change password |
| GET | `/my-donations` | Auth | Donation history |
| GET | `/notifications` | Auth | Notification list |
| POST | `/notifications/<id>/read` | Owner | Mark read |
| POST | `/notifications/read-all` | Auth | Mark all read |
| GET | `/admin` | Admin | Stats dashboard |
| GET | `/admin/users` | Admin | User management |
| POST | `/admin/users/<id>/suspend` | Admin | Suspend / reactivate |
| GET | `/admin/requests` | Admin | Request moderation |
| POST | `/admin/requests/<id>/remove` | Admin | Close/remove request |

### 12.2 JSON endpoints (progressive enhancement)

| Method | Path | Returns |
|---|---|---|
| GET | `/api/donors?group=&city=&page=` | `{items:[{id,name,blood_group,city,area,eligible,last_donation}], total, page}` — **no phone** |
| GET | `/api/requests?status=open&group=&city=` | Paginated public request cards |
| GET | `/api/notifications/unread-count` | `{count: 3}` |
| POST | `/api/profile/availability` | `{is_available: false}` |
| GET | `/api/stats` | `{donors, open_requests, donations, fulfilled}` |

Every JSON response uses an explicit serialiser (`to_public_dict()` / `to_private_dict()`), never `__dict__`. This prevents accidental PII leaks.

---

## 13. UI / UX Specification

### 13.1 Design tokens

| Token | Value |
|---|---|
| Primary (blood red) | `#C62828` |
| Primary dark | `#8E0000` |
| Accent (urgent) | `#F57C00` |
| Critical | `#B71C1C` |
| Success | `#2E7D32` |
| Surface | `#FFFFFF`, `#FFF8F7` |
| Text | `#1F2937`, muted `#6B7280` |
| Radius | `12px` cards, `8px` inputs, `999px` pills |
| Font | `system-ui, "Segoe UI", Inter, sans-serif` |
| Spacing scale | 4 / 8 / 12 / 16 / 24 / 32 / 48 px |

### 13.2 Page inventory

1. **Landing** — value proposition, blood-group quick search, stats, "How it works" (3 steps), safety disclaimer, CTA.
2. **Register / Login** — single-column card, inline validation, show/hide password.
3. **Onboarding profile** — blood group select, phone (with privacy note), city, DOB, last donation.
4. **Dashboard** — greeting, availability switch, unread notifications, my open requests, offers received, nearby compatible requests.
5. **Donor search** — sticky filter bar (group, city, available only, distance), result cards, empty state with "broaden search".
6. **Request list** — urgency chips, city, time remaining, "View" CTA.
7. **Request detail** — patient info, hospital, map placeholder, urgency banner, matched donors, offer list, owner actions.
8. **New request** — 2-column form on desktop; progressive disclosure; disclaimer checkbox.
9. **Profile** — personal details, privacy card ("your phone is hidden until you accept"), donation history.
10. **Notifications** — grouped by day, unread dot, mark-all-read.
11. **Admin** — KPI cards, filterable tables, destructive-action confirmations.
12. **Error pages** — 403, 404, 410 (expired request), 429, 500.

### 13.3 Accessibility & responsive rules

- WCAG 2.1 AA contrast; visible focus rings; all inputs have labels.
- Urgency is conveyed by text + icon, not colour alone.
- Tap targets ≥ 44×44 px; layout works at 375 px, 768 px, 1280 px.
- Forms have inline error text linked with `aria-describedby`; flash messages use `role="status"`.
- Respect `prefers-reduced-motion`.
- No autoplay, no carousel-only content, no icon-only buttons without `aria-label`.

---

## 14. Project Structure

```
bloodlink/
├── app/
│   ├── __init__.py              # create_app(config) factory
│   ├── config.py                # Dev / Test / Prod config classes
│   ├── extensions.py            # db, login_manager, csrf, limiter, mail, migrate
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── blood_request.py
│   │   ├── donor_response.py
│   │   ├── donation.py
│   │   ├── notification.py
│   │   └── auth_token.py
│   ├── blueprints/
│   │   ├── auth/routes.py + forms.py
│   │   ├── main/routes.py
│   │   ├── donors/routes.py
│   │   ├── requests/routes.py + forms.py
│   │   ├── offers/routes.py
│   │   ├── profile/routes.py + forms.py
│   │   ├── notifications/routes.py
│   │   └── admin/routes.py
│   ├── services/
│   │   ├── matching.py          # compatibility matrix + ranking
│   │   ├── eligibility.py       # cooldown, age, status
│   │   ├── notifications.py     # create + fan-out helper
│   │   ├── requests.py          # status transition guards
│   │   └── audit.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── macros/forms.html, cards.html
│   │   ├── auth/…, main/…, donors/…, requests/…, profile/…, admin/…
│   │   └── errors/403.html, 404.html, 429.html, 500.html
│   ├── static/
│   │   ├── css/tokens.css, base.css, components.css, pages.css
│   │   ├── js/app.js, donors.js, requests.js, notifications.js, validate.js
│   │   └── img/logo.svg, hero.svg, empty-state.svg
│   └── utils/
│       ├── validators.py        # blood group, phone, pincode
│       ├── decorators.py        # @admin_required, @owner_required
│       └── serializers.py       # public vs private dicts
├── migrations/                  # Flask-Migrate / Alembic
├── tests/
│   ├── conftest.py
│   ├── factories.py
│   ├── test_auth.py
│   ├── test_profile.py
│   ├── test_donors_search.py
│   ├── test_requests.py
│   ├── test_matching.py
│   ├── test_offers_privacy.py
│   ├── test_eligibility.py
│   ├── test_notifications.py
│   ├── test_admin.py
│   └── test_security.py
├── seed.py                      # demo donors + requests
├── run.py                       # entry point
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── PROJECT_PLAN.md              # this document
```

---

## 15. Security, Privacy & Compliance

### 15.1 Security controls

| Threat | Control |
|---|---|
| SQL injection | SQLAlchemy parameter binding; no f-string SQL |
| XSS | Jinja autoescaping on; never `|safe` on user input; sanitise `notes` |
| CSRF | Flask-WTF token on every state-changing form |
| Password theft | Scrypt/PBKDF2 hashing, min 8 chars + strength meter, no password in logs |
| Session hijack | `SESSION_COOKIE_HTTPONLY=True`, `SAMESITE='Lax'`, `SECURE=True` in prod, session rotation on login |
| Brute force | Flask-Limiter: 10/min on login, 5/15 min per account after failures |
| IDOR | Ownership checks in every route (`request.requester_id == current_user.id`) |
| Mass assignment | Explicit field whitelists in forms; never bind `role`, `status` from requests |
| Enumeration | Generic "Invalid email or password"; register response does not confirm email existence on reset |
| PII leak | `to_public_dict()` serialiser; phone masked in templates; no PII in logs/analytics |
| Spam requests | Rate limit 5 requests/day/user; admin removal; optional verified email |
| Malicious files | No uploads in v1 |
| Open redirect | Validate `next` is a relative path |
| Clickjacking | `X-Frame-Options: DENY`, CSP `frame-ancestors 'none'` |

### 15.2 Privacy rules (non-negotiable)

1. Donor phone is visible **only** to the requester and **only** after the donor's offer is accepted.
2. Requester phone is visible **only** to the accepted donor.
3. Admin can see phone only for moderation, and access is audit-logged.
4. Public/unauthenticated pages never list donors or phone numbers.
5. Search results never include phone numbers, exact address, or email.
6. Account deletion anonymises name/phone/email and closes open requests.

### 15.3 Medical & legal disclaimers (shown in UI)

> BloodLink is a community matching platform, not a blood bank or medical service. We do not test, store, transport, or sell blood. Eligibility shown here is informational only; final screening is performed by the hospital or licensed blood bank. In an emergency, contact the nearest hospital immediately.

Also: no payment for blood; report suspicious requests; data used only for matching.

---

## 16. Testing Strategy

### 16.1 Test pyramid

```
        ┌──────────────────────────┐
        │ Manual E2E / smoke (10%) │  browser walkthrough of critical flows
        ├──────────────────────────┤
        │ Integration (50%)        │  Flask test client + in-memory SQLite
        ├──────────────────────────┤
        │ Unit (40%)               │  matching, eligibility, validators, serialisers
        └──────────────────────────┘
```

- **Frameworks:** pytest, pytest-cov, freezegun (time travel), Flask test client.
- **Database:** in-memory SQLite created/dropped per test; `WTF_CSRF_ENABLED = False` in test config only.
- **Coverage targets:** ≥ 90% `services/`, ≥ 70% overall. CI fails below 70%.
- **Security checks:** `bandit -r app`, `pip-audit`, manual OWASP top-10 checklist.
- **Performance check:** seed 5,000 donors, assert donor search responds < 300 ms (local) and uses the composite index.

### 16.2 Automated test cases

#### A. Authentication (`tests/test_auth.py`)

| ID | Scenario | Input / action | Expected |
|---|---|---|---|
| TC-AUTH-01 | Register valid user | unique email, strong password | 302 → login/dashboard; user exists; password hashed |
| TC-AUTH-02 | Duplicate email (different case) | `Asha@x.com` then `asha@x.com` | 200 with field error; only 1 user row |
| TC-AUTH-03 | Weak password | `123456` | 200 with error; no user created |
| TC-AUTH-04 | Password mismatch | confirm ≠ password | 200 with error |
| TC-AUTH-05 | Invalid email format | `not-an-email` | 200 with error |
| TC-AUTH-06 | Login success | valid credentials | 302; session contains user id |
| TC-AUTH-07 | Login wrong password | valid email + bad password | 200 generic error; no session |
| TC-AUTH-08 | Protected route anonymous | `GET /dashboard` | 302 → `/auth/login?next=/dashboard` |
| TC-AUTH-09 | Logout | POST `/auth/logout` | session cleared; dashboard redirects |
| TC-AUTH-10 | Login rate limit | 6 failed attempts | 429 after threshold |
| TC-AUTH-11 | Reset token single use | use token twice | second use rejected |
| TC-AUTH-12 | Reset token expiry | token older than 60 min (freezegun) | rejected |
| TC-AUTH-13 | CSRF token missing | POST register without token (CSRF on) | 400 |

#### B. Profile & privacy (`tests/test_profile.py`)

| ID | Scenario | Expected |
|---|---|---|
| TC-PROF-01 | Update blood group A+ → O− | saved; search reflects new group |
| TC-PROF-02 | Invalid blood group `Z+` | 400 / form error, DB unchanged |
| TC-PROF-03 | Toggle availability off | `is_available=0`; donor hidden from search |
| TC-PROF-04 | Last donation date in future | validation error |
| TC-PROF-05 | Phone never rendered on public donor page | response body contains mask only |
| TC-PROF-06 | User edits another user's profile | 403 |
| TC-PROF-07 | DOB under 18 | marked ineligible to donate |

#### C. Donor search & matching (`tests/test_donors_search.py`, `test_matching.py`)

| ID | Scenario | Expected |
|---|---|---|
| TC-SRCH-01 | Filter by exact group O− | only O− donors returned |
| TC-SRCH-02 | A+ recipient compatibility | returns A+, A−, O+, O−; never B+ |
| TC-SRCH-03 | AB+ recipient | returns all 8 groups |
| TC-SRCH-04 | O− recipient | returns only O− |
| TC-SRCH-05 | Unavailable donor | excluded by default; visible with "include unavailable" flag (if enabled) |
| TC-SRCH-06 | Donor in cooldown | returned only when `eligible_only=false`; card shows "eligible from <date>" |
| TC-SRCH-07 | City filter case-insensitive | `pune` = `Pune` |
| TC-SRCH-08 | Pagination | page 1 and 2 disjoint, page size 20 |
| TC-SRCH-09 | Anonymous search | redirect to login (no data in body) |
| TC-SRCH-10 | SQLi payload in city | literal search, 200, no DB error, table intact |
| TC-SRCH-11 | Ranking | exact group + nearer + available ranks first |
| TC-SRCH-12 | JSON response shape | no `phone`, `email`, `password_hash` keys |

#### D. Blood requests (`tests/test_requests.py`)

| ID | Scenario | Expected |
|---|---|---|
| TC-REQ-01 | Create valid request | 302; row `status=open`; owner set from session |
| TC-REQ-02 | Missing hospital name | form error, no row |
| TC-REQ-03 | `units_needed=0` / `-1` / `11` | form error |
| TC-REQ-04 | `needed_by` in the past | form error |
| TC-REQ-05 | Unsafe `notes` (`<script>`) | stored escaped; not executed in detail page |
| TC-REQ-06 | Edit own open request | saved |
| TC-REQ-07 | Edit another user's request | 403 |
| TC-REQ-08 | Edit fulfilled/cancelled request | 400 / blocked |
| TC-REQ-09 | Cancel own request | `status=cancelled`; removed from open list |
| TC-REQ-10 | Expired request read | lazily set to `expired`; page shows expired state |
| TC-REQ-11 | Fulfil request without accepted offer | blocked |
| TC-REQ-12 | Fulfil with accepted offer | `status=fulfilled`, donation row created, donor cooldown set |

#### E. Offers, accept & contact reveal (`tests/test_offers_privacy.py`)

| ID | Scenario | Expected |
|---|---|---|
| TC-OFF-01 | Eligible donor offers | 302; response `offered`; requester notification created |
| TC-OFF-02 | Donor in cooldown offers | blocked with reason message |
| TC-OFF-03 | Duplicate offer | unique constraint handled gracefully, no 500 |
| TC-OFF-04 | Donor offers own request | 400 |
| TC-OFF-05 | Requester's page before accept | donor phone **absent**; masked only |
| TC-OFF-06 | Accept offer | `accepted`; request `matched`; both phones visible to each party |
| TC-OFF-07 | Non-owner accepts | 403; status unchanged |
| TC-OFF-08 | Decline offer | `declined`; phone still hidden |
| TC-OFF-09 | Donor withdraws | `withdrawn`; requester notified |
| TC-OFF-10 | Second offer after one accepted | blocked (request no longer open) |
| TC-OFF-11 | Accepted donor sees requester phone | visible exactly once, on request page only |

#### F. Donations & eligibility (`tests/test_eligibility.py`)

| ID | Scenario | Expected |
|---|---|---|
| TC-DON-01 | Record donation today | `last_donation_date=today`, `is_available=0` |
| TC-DON-02 | Eligibility on day 89 (freezegun) | false, reason `cooldown` |
| TC-DON-03 | Eligibility on day 91 | true |
| TC-DON-04 | Age 17 / 66 | ineligible |
| TC-DON-05 | Suspended user | ineligible and cannot log in |
| TC-DON-06 | Donation history totals | sums units, count correct |
| TC-DON-07 | Mark fulfilled twice | idempotent / blocked, no duplicate donation |

#### G. Notifications & admin (`tests/test_notifications.py`, `test_admin.py`)

| ID | Scenario | Expected |
|---|---|---|
| TC-NOT-01 | Read own notification | `is_read=1`; unread count decrements |
| TC-NOT-02 | Read another user's notification | 404/403 |
| TC-NOT-03 | Mark all read | unread count 0 |
| TC-ADM-01 | Non-admin visits `/admin` | 403 |
| TC-ADM-02 | Admin suspends user | user cannot log in; open offers withdrawn |
| TC-ADM-03 | Admin removes request | `cancelled`; hidden from public list |
| TC-ADM-04 | Dashboard stats | counts match fixtures |
| TC-ADM-05 | Audit entries | suspend/remove actions logged with actor |
| TC-ADM-06 | Admin changes own role via profile POST | ignored |

#### H. Security & non-functional (`tests/test_security.py`)

| ID | Scenario | Expected |
|---|---|---|
| TC-SEC-01 | Stored password | never equals plaintext; hash prefix recognised |
| TC-SEC-02 | Session cookie flags | HttpOnly true, SameSite Lax |
| TC-SEC-03 | Access another user's request by ID | 403 |
| TC-SEC-04 | `role=admin` injected in registration form | ignored, stays `user` |
| TC-SEC-05 | `next=//evil.com` after login | rejected, redirects locally |
| TC-SEC-06 | Security headers | `X-Frame-Options`, `X-Content-Type-Options`, CSP present |
| TC-UI-01 | 375 px viewport | no horizontal scroll; nav usable |
| TC-UI-02 | Keyboard-only flow | all actions reachable; focus visible |
| TC-NFR-01 | 5,000-donor search | < 300 ms local, index used |
| TC-NFR-02 | Page load (local) | < 2 s for dashboard with 50 requests |

### 16.3 Sample test code (copy-ready starting point)

`tests/conftest.py`

```python
import pytest
from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    def _make(email="asha@example.com", password="Str0ngPass!23", **kwargs):
        user = User(
            full_name=kwargs.pop("full_name", "Asha Rao"),
            email=email,
            phone=kwargs.pop("phone", "9876543210"),
            blood_group=kwargs.pop("blood_group", "O-"),
            city=kwargs.pop("city", "Pune"),
            pincode=kwargs.pop("pincode", "411001"),
            **kwargs,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _make


def login(client, email, password="Str0ngPass!23"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
```

`tests/test_auth.py`

```python
from app.models import User


def test_register_hashes_password(client, app):
    response = client.post(
        "/auth/register",
        data={
            "full_name": "New Donor",
            "email": "new@example.com",
            "password": "Str0ngPass!23",
            "confirm_password": "Str0ngPass!23",
            "blood_group": "A+",
            "phone": "9000000000",
            "city": "Pune",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    user = User.query.filter_by(email="new@example.com").first()
    assert user is not None
    assert user.password_hash != "Str0ngPass!23"
    assert user.check_password("Str0ngPass!23")


def test_duplicate_email_is_case_insensitive(client, make_user):
    make_user(email="Asha@Example.com")
    response = client.post(
        "/auth/register",
        data={
            "full_name": "Other",
            "email": "asha@example.com",
            "password": "Str0ngPass!23",
            "confirm_password": "Str0ngPass!23",
            "blood_group": "B+",
            "phone": "9000000001",
            "city": "Pune",
        },
    )
    assert response.status_code == 200
    assert b"already" in response.data.lower()
    assert User.query.count() == 1


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
```

`tests/test_matching.py`

```python
from app.services.matching import compatible_donor_groups

ALL_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


def test_a_positive_recipient_groups():
    assert set(compatible_donor_groups("A+")) == {"A+", "A-", "O+", "O-"}


def test_ab_positive_is_universal_recipient():
    assert set(compatible_donor_groups("AB+")) == ALL_GROUPS


def test_o_negative_recipient_only_gets_o_negative():
    assert compatible_donor_groups("O-") == ["O-"]


def test_o_negative_donor_is_universal():
    # O- must appear in every recipient's compatible list
    for recipient in ALL_GROUPS:
        assert "O-" in compatible_donor_groups(recipient)
```

`tests/test_eligibility.py`

```python
from datetime import date
from freezegun import freeze_time

from app.services.eligibility import is_eligible


@freeze_time("2026-01-01")
def test_cooldown_blocks_donor_for_90_days(app, make_user):
    donor = make_user(last_donation_date=date(2025, 12, 1))
    assert is_eligible(donor) is False


@freeze_time("2026-03-01")
def test_donor_is_eligible_after_cooldown(app, make_user):
    donor = make_user(last_donation_date=date(2025, 12, 1))
    assert is_eligible(donor) is True


@freeze_time("2026-01-01")
def test_unavailable_donor_is_not_eligible(app, make_user):
    donor = make_user(is_available=False)
    assert is_eligible(donor) is False
```

`tests/test_offers_privacy.py`

```python
from app.models import DonorResponse


def test_phone_is_hidden_until_offer_is_accepted(
    client, make_user, app
):
    requester = make_user(email="ravi@example.com", phone="9111111111", blood_group="A+")
    donor = make_user(
        email="asha@example.com", phone="9222222222", blood_group="O-",
        city="Pune",
    )
    blood_request = create_request(requester)  # test helper / factory
    offer = DonorResponse(request_id=blood_request.id, donor_id=donor.id)
    app.extensions["db"].session.add(offer)
    app.extensions["db"].session.commit()

    login(client, requester.email)
    page = client.get(f"/requests/{blood_request.id}").get_data(as_text=True)
    assert donor.phone not in page          # hidden before accept
    assert "92******22" in page             # masked value shown

    client.post(f"/offers/{offer.id}/accept", follow_redirects=True)
    page = client.get(f"/requests/{blood_request.id}").get_data(as_text=True)
    assert donor.phone in page              # revealed after accept
```

> Add a `create_request()` factory in `tests/factories.py` so each test file stays readable.

### 16.4 Manual E2E checklist (run before release)

| # | Step | Pass criteria |
|---|---|---|
| 1 | Register requester in a clean browser | account created, redirected to onboarding |
| 2 | Register donor in a private window | second account created |
| 3 | Donor sets O−, Pune, available, phone | profile saved |
| 4 | Requester posts A+ request in Pune | request visible in list, status open |
| 5 | Requester opens request → matched donors | O− Pune donor appears in ranked list, phone hidden |
| 6 | Donor opens request → "I can help" | offer appears; requester notification badge = 1 |
| 7 | Requester accepts offer | both phone numbers visible; request status matched |
| 8 | Requester marks fulfilled | donation recorded; status fulfilled |
| 9 | Donor dashboard | availability off; "eligible from +90 days" shown |
| 10 | Donor tries to offer another request | blocked with cooldown reason |
| 11 | Admin suspends donor | donor logged out, cannot log in |
| 12 | Mobile 375 px pass over all main pages | no overflow, all actions usable |
| 13 | Expired request (seeded past `needed_by`) | status expired, no offer button |

### 16.5 Commands

```powershell
# setup (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
flask --app run.py db upgrade

# seed demo data + run
python seed.py
flask --app run.py run --debug

# tests
pytest -q
pytest --cov=app --cov-report=term-missing --cov-fail-under=70
bandit -r app
pip-audit
```

---

## 17. Milestones & Timeline

Assumes one developer, part-time, ~6 focused hours/day.

| Phase | Deliverable | Est. |
|---|---|---|
| **0. Setup** | Repo, venv, app factory, config, extensions, base template, CI skeleton | 0.5 day |
| **1. Auth** | Models, register/login/logout, hashing, CSRF, rate limit, tests TC-AUTH | 2 days |
| **2. Profiles** | Profile CRUD, availability, eligibility service, public card, tests TC-PROF | 1.5 days |
| **3. Requests** | Request model/forms/routes, status machine, expiry, tests TC-REQ | 2 days |
| **4. Search & matching** | Compatibility matrix, ranking, filters, JSON API, tests TC-SRCH | 2 days |
| **5. Offers & contact** | Offer routes, accept/decline/withdraw, contact-reveal guard, notifications, tests TC-OFF/NOT | 2 days |
| **6. Donations & admin** | Donation recording, cooldown, admin console, stats, audit, tests TC-DON/ADM | 1.5 days |
| **7. UI polish** | Design tokens, responsive pass, accessibility, empty/error states | 1.5 days |
| **8. Hardening & release** | Security tests, seed data, README, full E2E, deployment | 1.5 days |
| **Total** | | **~14.5 days** |

Dependency order: `0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8`. Phases 7 and 8 overlap with 5–6 if time is tight.

Suggested checkpoints:
- **End of Phase 1:** a user can register and log in; all auth tests green.
- **End of Phase 4:** the core "find blood" story works end-to-end except contact reveal.
- **End of Phase 6:** full happy path works; privacy tests green.
- **End of Phase 8:** coverage ≥ 70%, E2E checklist signed off.

---

## 18. Definition of Done / Acceptance Criteria

A feature is done only when **all** are true:

- [ ] Works on desktop (1280 px) and mobile (375 px).
- [ ] Server-side validation + friendly error messages.
- [ ] Authorisation checks (owner/admin) verified by a test.
- [ ] No PII leak in HTML, JSON, or logs.
- [ ] Automated tests added and passing.
- [ ] Loading, empty, error, and success states handled.
- [ ] Keyboard accessible; labels and focus states present.
- [ ] Code formatted (`black`), linted (`ruff`), no `bandit` high findings.

**Release acceptance (MVP):**

1. A new visitor can register, complete a profile, and appear in compatible searches.
2. A requester can post a request and see compatible, eligible, nearby donors ranked.
3. A donor can offer; the requester can accept; contact is revealed only after accept.
4. Marking fulfilled records a donation and puts the donor on a 90-day cooldown.
5. Unauthorised users cannot read another user's phone, offers, or notifications.
6. All automated tests pass with ≥ 70% coverage; manual E2E checklist passes.
7. Landing page clearly states the no-sale / medical disclaimer.

---

## 19. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Phone number leak | High — safety & trust | `to_public_dict()`, masked templates, privacy tests, code review checklist |
| Fake or prank requests | High | Email verification, rate limits, admin removal, report button |
| Outdated availability | Medium | Self-toggle + 90-day cooldown + "last active" label + reminder email |
| Emergency misuse / liability | High | Prominent disclaimer, no medical claims, hospital-first messaging |
| Low donor supply at launch | High | Seed with partner NGOs, city-by-city launch, donation badges |
| Spam offers from one donor | Medium | Unique offer per request, offer rate limit, reputation score |
| SQLite write contention in prod | Medium | PostgreSQL in production from day one of public beta |
| Scope creep (chat, maps, payments) | Medium | Non-goals list; ship MVP first |
| Timezone/date bugs in cooldown | Medium | Store UTC, compute in one service, freeze-time tests |
| Legal issues with "selling blood" framing | High | Explicit no-payment policy; never add price fields |

---

## 20. Future Roadmap (post-MVP)

- **Phase 2:** PWA + push notifications, email/SMS alerts, map radius search, donor badges/leaderboard, report & moderation queue, field-level encryption, i18n (English/Hindi/Marathi).
- **Phase 3:** hospital/blood-bank accounts with verified inventory, appointment scheduling, camp discovery, ambulance/NGO partnerships.
- **Phase 4:** analytics for shortage forecasting (privacy-preserving aggregates), API for hospitals, native apps.

---

## 21. Appendix

### 21.1 Environment variables (`.env.example`)

```env
FLASK_ENV=development
SECRET_KEY=change-me-to-a-long-random-string
DATABASE_URL=sqlite:///bloodlink.db
# DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/bloodlink
DONATION_COOLDOWN_DAYS=90
PER_PAGE=20
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=no-reply@bloodlink.local
SESSION_COOKIE_SECURE=false
RATELIMIT_STORAGE_URI=memory://
```

### 21.2 Seed data plan (`seed.py`)

- 12 donors: at least one of every blood group, spread across Pune / Mumbai / Nagpur.
- 2 donors in cooldown, 1 unavailable, 1 suspended — to exercise filters.
- 3 requests: A+ critical (due in 6 h), O− urgent (due tomorrow), B+ normal (due in 3 days).
- 1 accepted offer + 1 fulfilled request with a donation, so dashboards are not empty.
- Admin account: `admin@bloodlink.local` / `Admin@12345` (dev only — force change in prod).

### 21.3 Requirement traceability

| Original requirement | Implemented by | Verified by |
|---|---|---|
| Find blood when needed | F-20 → F-37, §8 matching | TC-SRCH-01…12, TC-REQ-01, E2E 4–7 |
| Community helps each other | Donor registry, offers, accept flow | TC-OFF-01…11 |
| Register with email + password | F-01 → F-03 | TC-AUTH-01…09 |
| User 1 needs blood, User 2 has group, contact | Compatibility engine + consent-based reveal | TC-SRCH-02…04, TC-OFF-05/06/11 |
| HTML/CSS/JS + Flask + SQL | §9, §10, §11 | build + integration tests |
| Test cases for the site | §16 (55+ automated cases + E2E) | CI + manual checklist |

### 21.4 Glossary

| Term | Meaning |
|---|---|
| **Requester** | User who posts a blood request |
| **Donor** | User who offers to donate |
| **Offer / response** | Donor's "I can help" on a request |
| **Contact reveal** | Phone numbers shown to both parties after accept |
| **Eligibility** | Whether a donor may donate now (age, availability, cooldown) |
| **Cooldown** | 90-day wait after a donation |
| **Matched** | Request has an accepted donor |
| **Fulfilled** | Donation completed and recorded |

---

**Next step:** approve this plan, then build in the order in §17. Start with Phase 0–1 (project skeleton + auth) so every later feature has a working login, database, and test harness.
