# Design decisions

Why this code is shaped the way it is. Split out of the README to keep that
readable; the reasoning is here rather than dropped, because these are the
choices worth defending.

← [Back to the README](../README.md)

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
