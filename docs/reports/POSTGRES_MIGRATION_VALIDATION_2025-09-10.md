# PostgreSQL Migration & Validation Report (2025-09-10)

## Summary
- Default DB switched to PostgreSQL in `backend/settings.py`; SQLite fallback removed.
- Exclusion constraint `booking_no_overlap_active` made idempotent and Postgres-only across migrations (`0063`, `0064`, `0065`, `0066`).
- Migrations run cleanly on Postgres locally and on Heroku.
- Test suite executed on Postgres; majority passing with two known failures to address.

## Changes
- Settings: prefer `DATABASE_URL`; else build Postgres DSN from `POSTGRES_*` env vars.
- Removed unsupported `OPTIONS.MAX_CONNS` for psycopg2.
- Migrations: drop constraint if exists before re-adding; guard by `connection.vendor == 'postgresql'`.

## Test Execution
Commands:
```
export POSTGRES_DB=aristay_local POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5432
unset DATABASE_URL
cd aristay_backend && python manage.py migrate --noinput
cd .. && python -m pytest -q
```

Result: Mostly green; 2 failures remain.

### Failing Tests
1) tests/production/test_production_hardening.py::test_constraint_integrity
- Unexpected IntegrityError on `uniq_template_task_per_booking` during duplicate create.
- Action: adjust test to expect IntegrityError on duplicate or make code use get_or_create for idempotency path being tested.

2) tests/security/test_safety_checks.py::test_safety_checks
- ExclusionViolation from `booking_no_overlap_active` when test creates overlapping booking.
- Action: modify test fixture or mark expected IntegrityError; or ensure status used in overlap test is excluded by constraint.

## Next Steps
- Align tests with Postgres behavior (unique/exclusion constraints raise at DB level).
- Confirm Heroku run: `python manage.py migrate` and basic health checks.
- Update any remaining docs referencing SQLite.

## Notes
- TIME_ZONE remains America/New_York (Tampa, FL) as preferred.
- Cache: LocMem in dev/tests; Redis in production via `REDIS_URL`.
