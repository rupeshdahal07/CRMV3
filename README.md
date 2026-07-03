# Nobigo CRM — V3

An internal CRM for **Nobigo**, a Japanese-language learning business. It covers the full
admissions funnel and class management in one Django app:

> **Lead → Call → Consultation → Post-Consultation Call → Enrollment → Class Management
> (attendance, daily scoring, follow-ups)** — plus a separate, mobile-first **Student Portal**
> where enrolled students see their schedule, notices, leaderboard, and progress.

V3 is a ground-up re-architecture of CRMV2 with the **same feature set**, reorganised into clean
domain apps with a service/selector layer, and a **global design system built on Tailwind CSS**
matching the approved UI.

---

## What changed from V2 → V3

| Area | V2 | V3 |
|---|---|---|
| App layout | one monolithic `crm` app | 7 focused domain apps under `apps/` |
| Business logic | mixed into views | split into `services.py` (writes) + `selectors.py` (reads) |
| Settings | single `settings.py` | `config/settings/{base,dev,prod}.py`, env-driven |
| Styling | one hand-written `style.css` | Tailwind design system (`theme/` + `tailwind.config.js`) |
| Static/serving | dev only | WhiteNoise + hashed/compressed assets for production |
| Data-integrity fix | dashboard counted `status="Done"` (never matched) | corrected to `status="Completed"` |

Every screen, model, permission rule, custom-field behaviour, and the Student Portal from V2 is
present and verified (see **Testing** below).

---

## Architecture

```
CRMV3/
├── manage.py
├── config/                     # Django project (not an app)
│   ├── settings/{base,dev,prod}.py
│   ├── urls.py  wsgi.py  asgi.py
├── apps/
│   ├── core/                   # framework layer — no domain data of its own
│   │   ├── models.py           #   FieldDefinition + shared mixins
│   │   ├── registry.py         #   module config that drives generic CRUD
│   │   ├── views.py            #   generic list/create/edit/delete + dashboard + fields
│   │   ├── permissions.py      #   role rules + teacher record-scoping
│   │   ├── custom_fields.py    #   FieldDefinition -> form field injection
│   │   ├── navigation.py       #   permission-aware sidebar
│   │   ├── selectors.py        #   dashboard queries
│   │   └── context_processors.py, decorators.py, templatetags/
│   ├── accounts/               # User model, auth backend, student accounts, user admin
│   ├── leads/                  # Lead, IntakeTarget, choices, lead detail + timeline
│   ├── consultations/          # ConsultationSlot, Consultation, PostConsultationCall
│   ├── cohorts/                # Curriculum, Cohort, ClassEvent, Enrollment, DailyScore, Followup
│   ├── scoring/                # daily scoring + leaderboard (views + service, no models)
│   └── portal/                 # student portal (views + selectors, no models)
├── templates/                  # all templates, grouped by area
├── theme/input.css             # Tailwind entry (base + component layer)
├── tailwind.config.js          # THE design system (colours, radii, shadows, fonts)
└── static/css/app.css          # compiled output (committed so it runs without Node)
```

**Dependency direction:** domain apps depend on `core` (mixins, permissions); `core.registry`
wires the domain forms/models into the generic engine. Cross-app model references use string FKs
(`"leads.Lead"`), so migrations are order-independent.

**The generic CRUD engine.** Most list/create/edit/delete screens are config, not code. To add a
module, add an entry to `apps/core/registry.py::MODULES` (model, form, columns, filters, optional
parent/detail) — you get search, filtering, teacher-scoping, custom fields, and consistent UI for
free.

**Custom fields.** Admins add fields to any module via **Manage Fields** with no migration; values
live in each record's `custom_data` JSON and are injected into the form by
`apps/core/custom_fields.py`.

**Roles.** `Admin, Support, Teacher, Tester, Student`. Admin/Support/Teacher use the staff CRM;
Students are auto-provisioned a login when their Lead is created and are routed to `/portal/`.
Teachers are scoped to their own cohorts everywhere. Full matrix in `apps/core/permissions.py`.

---

## Quick start (local development)

Requires **Python 3.12+** and **Node 18+** (Node only to rebuild CSS).

```bash
# 1. Python env
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 2. CSS (optional — a compiled static/css/app.css is committed)
npm install
npm run build                     # or: npm run watch  (rebuild on template change)

# 3. Database + demo data
python manage.py migrate
python manage.py seed_demo        # 2 leads, a cohort with 14 scored days, etc.
python manage.py backfill_student_accounts

# 4. Run
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and sign in. `seed_demo` creates staff logins with the password
**`nobigo123`**:

| Username | Role | Sees |
|---|---|---|
| `admin` | Admin | everything, `/admin/`, Manage Fields, Users |
| `sujata` | Support | admissions funnel, leads, follow-ups |
| `sanjit` | Teacher | only their cohorts, scoring, leaderboard |

Student logins are auto-generated (e.g. `asim358`); view/set any student's credentials from their
Lead detail page → **Manage login**.

### Testing on a phone (same WiFi)

```bash
python manage.py runserver 0.0.0.0:8001
```

Then browse to `http://<your-LAN-IP>:8001/`. `ALLOWED_HOSTS=['*']` in dev only — see **Production**.

---

## The design system

`tailwind.config.js` is the single source of truth for the theme, taken from the approved UI:

- **Brand** `#6d5efc` (+ `brand-soft #efedff`), **ink** `#17171c`, **canvas** `#ecedf1`
- Semantics: `success #1f9d57`, `danger #e5484d`, `amber #d98324`, `accent #e5734d`
- Radii `card:16px / shell:22px`, soft `shadow-card` / elevated `shadow-shell`, **Inter** font

Reusable component classes (`.btn-*`, `.card`, `.chip-*`, `.input`, `.nav-link`, `.pill-*`) are
defined in `theme/input.css` so templates stay semantic. Change a token once in the config and it
propagates everywhere. Rebuild with `npm run build`.

---

## Production

Use the production settings and set real secrets via environment variables:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
export DJANGO_SECRET_KEY="<50+ random chars>"
export DJANGO_ALLOWED_HOSTS="crm.nobigo.jp"
export DATABASE_URL="postgres://user:pass@host:5432/nobigo"   # requires psycopg + dj-database-url

python manage.py migrate
python manage.py collectstatic --no-input        # WhiteNoise hashes + compresses
gunicorn config.wsgi:application
```

`prod.py` forces `DEBUG=False`, HTTPS redirect, secure cookies, HSTS, and refuses to boot with the
insecure dev secret key. SQLite is fine for a pilot; move to **Postgres** for real concurrent use.

---

## Testing / verification

The backend and every screen were exercised with Django's test client across all roles (dashboard,
all 11 CRUD modules, all detail pages, scoring, leaderboard, custom fields, users, and the 5 portal
pages) plus write-path checks: lead-create auto-provisions a student account, custom-field values
round-trip through `custom_data`, and daily-scoring correctly raises a needs-attention follow-up and
seeds documentation status. Run the app with `seed_demo` and click through each role to explore.
