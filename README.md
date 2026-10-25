# Car Dealership Inventory System

[![CI](https://github.com/sanianixon/Car_Dealership_Inventory/actions/workflows/ci.yml/badge.svg)](https://github.com/sanianixon/Car_Dealership_Inventory/actions/workflows/ci.yml)

A full-stack vehicle inventory system: a token-authenticated REST API over a real
database, and a React single-page app for browsing, searching and buying stock.

Built test-first for the Incubyte TDD kata. **143 tests — 95 on the backend at
99% statement coverage, 48 on the frontend** — and a commit history of 9 RED /
9 GREEN / 2 refactor steps that shows how the code actually got here.

---

## Contents

- [What it does](#what-it-does)
- [Stack](#stack)
- [Running it locally](#running-it-locally)
- [Running the tests](#running-the-tests)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [API reference](#api-reference)
- [Design decisions](#design-decisions)
- [What the tests cover](#what-the-tests-cover)
- [Known limitations](#known-limitations)
- [My AI Usage](#my-ai-usage)

---

## What it does

- Register and sign in; every vehicle and inventory route requires a valid JWT.
- Browse the catalogue of models, sold out or not, ordered by make then model.
  Each card advertises the cheapest car available, the colours on the lot and
  how many are left.
- Open a model to see **the actual cars** behind it — each with its own build
  year, colour, owner count, arrival date and price — and buy a specific one.
- Search by make, model, category and price range, combined with AND. A price
  filter matches against the cars themselves, so it only finds models with a
  car in range still for sale.
- **A car is sold exactly once, even when several buyers reach it at the same
  instant** — see [Design decisions](#design-decisions).
- Administrators can list models, edit them, take more cars in and delete.
  Ordinary users cannot, and are refused by the API, not merely by a hidden
  button.

## Stack

| Layer | Choice |
| --- | --- |
| API | Python 3.11, FastAPI 0.162, SQLAlchemy 2.1 |
| Database | SQLite file (a real database on disk, not in-memory) |
| Auth | JWT (PyJWT, HS256) with bcrypt password hashing |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS v4, React Router 7 |
| Backend tests | pytest 9.1 + pytest-cov — 95 tests, 99% coverage |
| Frontend tests | Vitest 3.2 + Testing Library + jsdom — 48 tests |

## Running it locally

Verified by cloning this repository fresh and following these steps.

### Prerequisites

- **Python 3.11 or newer.** Check with `python3 --version`. On 3.9 or 3.10 the
  install fails with a confusing message about `annotated-types`, because the
  pinned dependencies have no build for those versions, and the code uses
  `X | None` annotations at runtime. If your `python3` is older, use an explicit
  interpreter below (`python3.11 -m venv venv`).
- **Node 20 or newer.** Check with `node --version`.

### 1. Backend

```bash
cd backend
python3 -m venv venv              # or: python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Seed an administrator and a starter catalogue (safe to run more than once):

```bash
python scripts/seed.py
```

That creates `admin@dealership.com` / `Admin#12345`, plus 14 vehicles — two of
them deliberately out of stock, so the disabled Purchase button is visible
straight away.

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: <http://localhost:8000/docs>

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The dev server proxies `/api` to port 8000, so
there is no CORS setup and no base URL to configure. If your backend runs
elsewhere, set `VITE_API_TARGET`.

### Configuration

Every variable has a working default for local development.

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./dealership.db` | Any SQLAlchemy URL |
| `JWT_SECRET` | a development key | **Required** when `APP_ENV=production`; the app refuses to start on the default |
| `APP_ENV` | `development` | Set to `production` to enforce the above |
| `ADMIN_SIGNUP_CODE` | unset | When set, registering with a matching `adminCode` grants admin. While unset, every code is rejected |
| `VITE_API_TARGET` | `http://localhost:8000` | Backend the dev server proxies to |

## Running the tests

Backend:

```bash
cd backend
source venv/bin/activate
pytest -v                                      # 95 tests
pytest --cov=app --cov-report=term-missing     # coverage
```

Frontend:

```bash
cd frontend
npm test                                       # 48 tests
npm run test:coverage                          # coverage
```

Both run on every push — see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml). The committed output of
the backend command is in [`docs/test-report.txt`](docs/test-report.txt).

```
95 passed
TOTAL   551 statements   6 missed   99% coverage
```

The six uncovered statements are the `get_db` request dependency and the
start-up lifespan hook, both replaced by the test fixtures. Testing them would
assert on the test setup rather than on the application, so they are left alone
deliberately rather than padded with hollow tests.

## Screenshots

| | |
| --- | --- |
| ![Sign in](docs/screenshots/01-signin.png) | ![Dashboard](docs/screenshots/02-dashboard.png) |
| **Sign in** — register and login share one card | **Dashboard** — the catalogue, ordered by make |
| ![Search](docs/screenshots/03-search.png) | ![Sold out](docs/screenshots/04-sold-out.png) |
| **Search** — filters combine with AND | **Sold out** — Purchase is disabled at zero stock |
| ![Model page](docs/screenshots/05-model-page.png) | ![Coverage](docs/screenshots/06-coverage.png) |
| **A model's own page** — the actual cars, each bought on its own | **Coverage** — backend, 95 tests at 99% |

## Architecture

```
HTTP  ─▶  routers/        request and response shapes, status codes
          services/       business rules, raises domain errors
          repositories/   all SQL; the only layer that holds a Session
          models.py       listings, cars, and database constraints
```

Each layer only knows the one beneath it:

- **Routers** translate HTTP to calls and back. They never build a query.
- **Services** own the rules. They raise `VehicleNotFoundError` or
  `OutOfStockError` and never mention a status code, so they are usable outside
  a web request — which is exactly what [`scripts/seed.py`](backend/scripts/seed.py)
  does, driving `VehicleService` directly with no HTTP involved.
- **Repositories** own the SQL. Changing the storage engine means rewriting one
  class and nothing above it.
- **`errors.py`** maps every failure — raised `HTTPException`, request
  validation, and domain errors — onto one response shape, so no route formats
  an error itself.

Dependencies are assembled per request in [`deps.py`](backend/app/deps.py), so
routes depend on a service rather than on a database session and a test can
replace either one.

## API reference

All paths are under `/api`. Every route except register and login needs
`Authorization: Bearer <token>`.

| Method | Path | Access | Body | Success |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | public | `{email, password, adminCode?}` | `201 {user}` |
| POST | `/auth/login` | public | `{email, password}` | `200 {token, user}` |
| GET | `/auth/me` | user | | `200 {user}` |
| GET | `/vehicles` | user | | `200 {vehicles}` |
| GET | `/vehicles/search` | user | query: `make, model, category, minPrice, maxPrice` | `200 {vehicles}` |
| GET | `/vehicles/{id}` | user | | `200 {vehicle}` **with its cars** |
| POST | `/vehicles` | **admin** | `{make, model, category, units: [car, …]}` | `201 {vehicle}` |
| PUT | `/vehicles/{id}` | **admin** | any subset of make/model/category | `200 {vehicle}` |
| DELETE | `/vehicles/{id}` | **admin** | | `204` |
| POST | `/vehicles/{id}/purchase` | user | `{unitId?}` | `200 {vehicle, unit}` |
| POST | `/vehicles/{id}/restock` | **admin** | `{units: [car, …]}` | `200 {vehicle, restocked, units}` |

The catalogue has two levels, because a dealership's stock has two levels. A
**listing** is a model; its price and stock are derived from the cars it holds:

```json
{ "id": "…", "make": "Maruti", "model": "Swift", "category": "Hatchback",
  "price": 480000.0,
  "quantity": 4,
  "colours": ["Fire Red", "Granite Grey", "Lucent Orange", "Pearl White"],
  "createdAt": "…", "updatedAt": "…" }
```

`price` is the **cheapest car currently available** — the figure a forecourt
advertises — and `quantity` is how many are left. Neither is stored, so a card
can never advertise stock the lot has already sold.

A **car** is one physical vehicle, returned by `GET /api/vehicles/{id}`:

```json
{ "id": "…", "year": 2019, "colour": "Lucent Orange", "price": 480000.0,
  "ownershipNumber": 3, "acquiredOn": "2026-07-21", "isAvailable": true }
```

`ownershipNumber` counts owners the way Indian used-car listings do, where 1 is
the first owner. `acquiredOn` is the day the dealership took that car in, and
cannot be in the future. `year` accepts next year, because new models reach a
forecourt before their model year starts.

Errors always use one shape, so the frontend has a single thing to parse:

```json
{ "error": { "message": "Validation failed",
             "details": [{ "path": "price", "message": "cannot be negative" }] } }
```

| Status | Meaning |
| --- | --- |
| 400 | Validation failed (`details` names each bad field) |
| 401 | Missing, invalid or expired token; bad credentials |
| 403 | Authenticated but not an administrator |
| 404 | No such vehicle |
| 409 | Duplicate email, or not enough stock |

## Design decisions

### A listing is not a car

The first version of this modelled a vehicle as one row with a `quantity`,
which is what the brief literally describes. It produced four Honda Citys that
shared a single build year, a single colour and a single owner history —
nonsense, because those describe *one car*, not a model.

So the catalogue is two tables. A `Vehicle` is a listing: Honda City, a sedan.
A `VehicleUnit` is one car on the lot, with its own year, colour, owner count,
arrival date and price. A listing's `quantity` and `price` are **derived** from
its available units rather than stored, so the two cannot drift apart: selling
the cheapest Swift raises the advertised from-price automatically, with no code
to keep in step.

This diverges from the brief, which specifies a vehicle with a stored
`quantity`. The read shape is preserved — `GET /api/vehicles` still returns
`{id, make, model, category, price, quantity}` — so the divergence is in how
stock is represented, not in what the API promises. It is a deliberate choice
that a used-car dealership cannot be modelled honestly any other way, and one I
would rather defend than a catalogue that claims four identical cars.

### Purchasing is one guarded statement, not read-then-write

The obvious implementation reads a car, checks it is unsold, then marks it
sold. Under concurrency that sells the same car twice: several buyers pass the
check before any of them writes. So the check and the write are a single
statement, and the number of rows it affects is the answer:

```sql
UPDATE vehicle_units SET sold_at = :now WHERE id = :id AND sold_at IS NULL
```

Zero rows affected means the guard refused — somebody else bought that car
first. It can never mean a car sold twice.

A buyer who names no car is a separate case. Ten buyers asking for "a Swift"
when four are on the lot must result in four sales, not one, so the service
tries the available cars cheapest-first and takes the first it can still claim.
Losing the race for one car is not a reason to refuse the sale while others are
free. **That bug was in the first version of this code and a concurrency test
caught it:** ten buyers all picked the same cheapest car, one won, and the other
nine gave up.

**The test for this is the one I would point at first.** An earlier version of
it passed against a deliberately broken read-then-write implementation, because
FastAPI's `TestClient` drives the app through a single blocking portal and
serialises the requests — so there was never any contention to catch. The real
test in [`test_concurrency.py`](backend/tests/test_concurrency.py) drives the
service directly, each buyer on its own session, all released by a barrier once
every one of them has read the stock. It was then confirmed in both directions:

| Implementation | 10 buyers, 1 car | 10 buyers, same car named | 10 buyers, 3 cars |
| --- | --- | --- | --- |
| Guarded `UPDATE` | 1 sold | 1 sold | 3 sold |
| Guard removed | **5 sold** | **4 sold** | **10 sold** |

The same class of bug exists in registration, where two requests can both find
an email unused. There the unique index is the real guarantee, so
`IntegrityError` is caught and returned as the same 409 rather than a 500.

### Privilege cannot be requested

`RegisterRequest` has no `role` field at all, so escalation is impossible by
construction rather than by filtering an unwanted value. Admin comes from an
invite code compared with `secrets.compare_digest`, or from the seed script. A
code is accepted only when `ADMIN_SIGNUP_CODE` is both set and matching, so an
unset variable can never be read as "any code works".

`require_admin` reads the role from the database row rather than the token's
claim, so an account that loses admin loses it immediately instead of when its
token expires. For the same reason `get_current_user` looks the subject up on
every request: a correctly signed token whose user has been deleted is rejected.

### Login failures are indistinguishable

An unknown email and a wrong password return byte-identical 401s, so the
endpoint cannot be used to discover which addresses have accounts. When no user
matches, the password is still hashed against a fixed dummy value, because
otherwise the response time alone would leak the answer. `LoginRequest`
deliberately has no password-length rule for the same reason — a 400 would
reveal that the policy, not the credentials, was the problem.

### Search treats input as data

`%` and `_` are wildcards in SQL `LIKE`, so a search for `100%` would otherwise
match everything. They are escaped and the query declares `ESCAPE`. Values are
bound as parameters and never concatenated, which a test asserts by searching
for `'; DROP TABLE vehicles; --` and checking the table survives.

### Other choices worth naming

- **Sold-out models are listed.** "All available vehicles" is read as the whole
  catalogue, because the dashboard needs the sold-out ones in order to show a
  disabled Purchase button at all.
- **The card's Purchase button opens the model's page.** The brief asks for a
  Purchase button on each vehicle, disabled at zero stock, and that is exactly
  what the card has. Clicking it hands over to the model's own page to choose
  *which* car, because "buy a Swift" is not a complete instruction when four
  different Swifts are on the lot.
- **Restocking takes cars, not a count.** A used-car lot is restocked by a
  specific car arriving with its own history and price, so `/restock` accepts
  units rather than a number.
- **Changing the catalogue is admin-only throughout**, not just for `DELETE` and
  restock. The brief marks only those two explicitly, and `POST`/`PUT` were at
  first left open to any signed-in user on that reading. That was wrong, for a
  reason worth recording: the UI already showed add and edit to administrators
  only, so the sole thing stopping a buyer adding stock to the dealership was a
  hidden button. A permission enforced in the interface is not a permission.
  This README asserted both positions at once before anyone noticed. Now the
  guard is on the route and three tests hold it there.
- **Constraints live in the database too.** `CHECK (quantity >= 0)` and
  `CHECK (price >= 0)` back up the request schemas, because validation protects
  the API while constraints protect the data from every other writer.
- **Validation rejects stringified numbers.** `"18500"` for a price is a 400
  rather than a silent coercion, since quietly accepting it hides a caller bug.
- **An empty `PUT` body is a 400.** It almost always means the request was built
  wrongly, and succeeding silently would hide that.
- **No router on the frontend.** There are two states, decided by whether anyone
  is signed in. A routing library would add a dependency without adding
  behaviour.

## What the tests cover

| File | Tests | Focus |
| --- | --- | --- |
| `test_vehicles.py` | 22 | Listing CRUD, validation, admin-only create/edit/delete |
| `test_inventory.py` | 14 | Buying a named or cheapest car; restocking |
| `test_search.py` | 13 | Filters, price bounds, LIKE escaping, injection |
| `test_vehicle_details.py` | 13 | Per-car history, and stock/price derived from it |
| `test_auth.py` | 8 | Registration, duplicates, login, JWT claims |
| `test_current_user.py` | 8 | Token identity, admin invite code |
| `test_edge_cases.py` | 7 | Paths that only run when something is wrong |
| `test_errors.py` | 3 | The uniform error envelope |
| `test_seed.py` | 4 | The seed script is idempotent and its cars genuinely differ |
| `test_concurrency.py` | 3 | Selling one car twice, under real contention |

Every backend test gets its own temporary SQLite file, so no test can leak state
into another.

On the frontend:

| File | Tests | Focus |
| --- | --- | --- |
| `VehicleCard.test.tsx` | 13 | Purchase disabled at zero stock, from-price, stock wording, admin controls hidden from buyers |
| `format.test.ts` | 11 | Indian digit grouping, dates that do not shift timezone, time on the lot |
| `api.test.ts` | 10 | Bearer token, error envelope to `ApiError`, blank filters dropped, 204 handling |
| `AuthScreen.test.tsx` | 7 | Server messages surfaced, field errors beside their field, admin code handling |
| `SearchBar.test.tsx` | 7 | Filters preserved per keystroke, whitespace treated as unfiltered |

The disabled-button test was checked by removing the `soldOut` guard from the
component and confirming three tests failed, rather than trusting a green run.
That mattered: without the guard the button still *looked* sold out — greyed,
muted, with an explanatory tooltip — and clicking it bought a car with no stock.
A screenshot would have looked entirely correct.

## Known limitations

Stated rather than hidden; each is a deliberate trade for a kata-sized project.

- **Frontend test coverage is narrower than the backend's.** The card, the API
  client and the forms are tested; `Dashboard.tsx`, which orchestrates loading,
  searching and the write operations, is covered only by TypeScript, ESLint and
  manual checking. It is the component most worth testing next.
- **No end-to-end tests.** Backend and frontend are each tested in isolation.
  The two were checked against each other by hand and with a scripted pass over
  the live API, not by an automated browser test.
- **The token lives in `localStorage`**, so any XSS on the origin can read it.
  An httpOnly cookie with CSRF protection would be the production answer.
- **Prices are floats.** Fine here; production money should be integer minor
  units — paise, in this case.
- **A sold car is kept, not deleted.** `sold_at` is stamped rather than the row
  removed, which keeps the history and is what makes a car claimable exactly
  once. The model page shows them under "Recently sold".
- **No per-car editing.** An administrator can list a model, take cars in and
  delete a listing, but cannot correct a typo in one car's colour without
  removing it. The endpoint is a small addition; it simply is not there yet.
- **No refresh tokens, rate limiting or account lockout.** A token simply
  expires after 8 hours.
- **SQLite** suits a single-process kata. The purchase guard is plain SQL and
  works the same on PostgreSQL, but SQLite serialises writers.

## My AI Usage

**Tool used:** Claude (Opus 5) via Claude Code, the terminal CLI, in VS Code.
There were three sessions: planning on claude.ai, a context-review session, and
the implementation. All three are reproduced verbatim in
[`PROMPTS.md`](PROMPTS.md), which is generated from the raw session
transcripts by [`docs/make_prompts.py`](docs/make_prompts.py). That script is
committed deliberately: it means "unedited" is checkable rather than merely
claimed, since anyone can re-run it and compare.

**The division of labour.** Claude wrote most of the code in this repository:
the FastAPI application, the test suite, the seed script and the React
frontend, one red/green step at a time. I ran the tests and made every commit
myself. What I want to be judged on is not that — it is the decisions, because
those are what the code is *for*, and they were mine.

**The decisions I made, and why.**

- **A listing is not a car.** The first version followed the brief literally: a
  vehicle row with a `quantity`. When provenance fields were added it put a
  build year, a colour and an owner count on that row, and the dashboard then
  showed four Honda Citys all built in the same year, the same colour, with the
  same owner. I stopped the work and said that made no sense — four cars on a
  forecourt are four different cars. That became the two-level model this
  project now runs on, and it is the change I would most want to talk about.
  It also meant accepting a deliberate divergence from the brief, which I
  decided was worth it and documented rather than hid.
- **Inventory management is admin-only throughout.** `POST` and `PUT` were left
  open to any signed-in user on a literal reading of the brief. I judged that
  wrong: the UI already hid those controls from buyers, so the only thing
  stopping a buyer adding stock was a hidden button. Tightening it broke 35
  tests, which turned out to be worth knowing.
- **The interface was generic.** The first version worked and looked like every
  other generated dashboard — centred card, rounded corners, teal accent. I
  said so, chose the direction for the redesign, and reviewed each pass.
- **Scope.** A thoroughly tested backend over a broad shallow one; how far to
  take the frontend; when to stop adding features.
- **Honesty under pressure.** I asked at one point whether the AI co-author
  trailers could come off. They could have; I left them on. When one commit
  lost its trailer to a broken terminal paste, I chose to record the omission
  rather than rewrite pushed history to look tidier.
- **Verification.** Claude has no browser, so every judgement about whether the
  application actually worked was mine: I drove it by hand, took the
  screenshots, and more than once sent back something that was wrong on screen
  while passing its tests.

**What AI got wrong, and how it surfaced.** This is the part I found most
instructive.

- The first concurrency test was **worthless and looked fine**. It passed, so it
  read as proof the purchase was atomic. Claude proposed checking it by
  substituting a deliberately broken implementation — which passed the test
  unchanged. The cause was `TestClient` serialising requests. The test was
  rewritten to drive the service directly and verified in both directions. A
  green test is not evidence until you have watched it fail.
- Two commits were **silently lost**. Multi-line commit messages pasted into the
  terminal as heredocs broke mid-paste, leaving the shell stuck at a `heredoc>`
  prompt swallowing everything typed after it. I reported "done" twice in good
  faith while nothing had actually run. It was caught by checking `git log`
  rather than trusting the report. We switched to writing messages to a file and
  committing with `git commit -F`.
- Carried-over notes claimed a previous version of this project existed on disk
  to reuse a frontend from. It did not, so the frontend was built from scratch.
- A seeded email of `admin@dealership.test` could not work at all: `.test` is a
  reserved TLD that `email-validator` rejects.

**On the commit trailers.** Every commit here was AI-assisted and carries
`Co-Authored-By: Claude Opus 5`, with one exception. Commit `9b0fc26` is missing
its trailer: the message was pasted into the terminal and truncated at exactly
that line, which is also what jammed the shell. Its body still states the AI
involvement in prose. Rather than rewrite already-pushed history over one line, I
chose to record the omission — in commit `ddf5810`, and here.

**Reflection.** The useful lesson was not that AI is fast. It is that speed is
the risk: it produces plausible work faster than anyone can review it, and
every bad moment in this project was a green signal that meant nothing — a test
that could not fail, commits that were never made, a type check that checked no
files, a CI step asserting on a print statement. None of those were caught by
reading the code more carefully. They were caught by insisting on evidence:
break the implementation and watch the test catch it, read `git log` instead of
trusting "done", run the API against a real server rather than only the test
client.

The other lesson is about where the work actually is. The code was the cheap
part. Deciding that a listing is not a car, that a permission enforced in the
interface is not a permission, that an interface which merely works is not
finished — none of that came out of a prompt, and none of it would have been
caught by a faster model. That is the part I would bring to a team, and the
part I would want to be asked about.

---

## Repository layout

```
backend/
  app/
    main.py            application, error handlers, lifespan
    database.py        engine, session factory, get_db dependency
    models.py          User, Vehicle (a listing) and VehicleUnit (one car)
    schemas.py         request/response models and shared field types
    security.py        bcrypt hashing, JWT issuing and verification
    deps.py            get_current_user, require_admin, service wiring
    errors.py          the single error envelope
    routers/           auth.py, vehicles.py
    services/          vehicle_service, inventory_service, exceptions, lookup
    repositories/      vehicle_repository (all SQL, including the claim)
  scripts/seed.py      idempotent admin + starter catalogue
  tests/               95 tests, including test_concurrency.py
frontend/
  src/
    api.ts             the only module that calls the API
    auth.tsx           auth provider
    auth-context.ts    context and useAuth hook
    format.ts          rupees and Indian dates, in one place
    components/        AuthScreen, Dashboard, VehicleCard, UnitCard,
                       SearchBar, VehicleForm, RestockForm, Modal
    pages/ModelPage    one model's cars, where a purchase happens
docs/
  test-report.txt      committed pytest + coverage output
  screenshots/
PROMPTS.md             raw AI conversation logs
```
