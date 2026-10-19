# Deployment notes

This project is not deployed anywhere. These notes say what running it needs, so nobody has to
guess.

## What it needs

- **PostgreSQL 14 or newer.** SQLite is not supported: the reporting query uses PostgreSQL-only
  syntax (`::numeric`), and the schema relies on foreign keys with cascading deletes and CHECK
  constraints.
- **A fixed `SECRET_KEY`.** If it is unset, the server generates a random key each time it
  starts, so every token stops working on restart. The same happens with more than one worker
  process: each would generate its own key and reject the others' tokens.
- **`DEFAULT_ADMIN_PASSWORD`** to seed the single sign-in account. There is no registration
  endpoint, so without this nobody can sign in.
- **`CORS_ORIGINS`** if the frontend is served from a different origin than the API. It takes a
  JSON list, for example `CORS_ORIGINS='["https://app.example.com"]'`. The default allows only the
  local development origins.
- **`VITE_API_URL`** when the frontend is built, only if the API is on a different origin from the
  frontend. It is baked into the JavaScript bundle at build time. Unset, a production build uses
  the page's own origin.

## Local development

See *Setup* in the [README](README.md): create the database, copy `.env.example` to `.env`, then
run the backend and the frontend.

## Docker

The `Dockerfile` builds the frontend, then serves it from the FastAPI app:

```bash
docker build -t sip-friction-analyzer .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg2://user:password@host:5432/sip \
  -e SECRET_KEY=<a-long-random-value> \
  -e DEFAULT_ADMIN_PASSWORD=<a-password> \
  sip-friction-analyzer
```

The container needs a PostgreSQL it can reach; there is no `docker-compose.yml`. `.dockerignore`
keeps a local `.env` out of the image, so pass settings at run time as above.

**Status.** The image is built and run in CI. The job "Docker Image Build & Smoke Test" in
`.github/workflows/ci.yml` builds this `Dockerfile` on a Linux runner, starts the container against a
PostgreSQL service, and checks that a wrong password is refused, the seeded account signs in, a
simulation runs, an invalid pause is rejected with a 422, the built frontend is served at `/`, and the
tables were created. It also checks that the image holds no `.env`, that no secret is set in its
configuration or build history, and that the process does not run as root. What this does not show:
it has not been run on the author's own computer (Docker is not installed there), and nothing has
been deployed to a host, so HTTPS, a different origin for the frontend and a hosted database are
untested.

Use a `SECRET_KEY` of at least 32 bytes. A shorter key works but makes PyJWT log an
`InsecureKeyLengthWarning`, as the CI job's throwaway key does.

A production build of the frontend calls the API on its own origin, so the image works from any
host name with no `VITE_API_URL`. Set `VITE_API_URL` at build time only if the API is hosted
elsewhere. The dev server (`npm run dev`) still defaults to `http://localhost:8000`.

## Render

`render.yaml` is a Render Blueprint for a Docker web service built from the `Dockerfile`. The
database is a separate free PostgreSQL on [Neon](https://neon.tech), because Render's own free
database is deleted after 30 days.

1. In Neon, create a project and copy its connection string (`postgresql://...?sslmode=require`).
2. In Render choose *New > Blueprint*, pick this repository, and enter `DATABASE_URL` (the Neon
   string) and `DEFAULT_ADMIN_PASSWORD` when asked. `SECRET_KEY` is generated for you.

Both free tiers stay free with no expiry, with two limits. The Render web service sleeps after
about 15 minutes idle, so the next request takes up to a minute. Neon suspends its compute when
idle and wakes on the next connection, and the free plan has a small storage cap. Neither is a
substitute for backups.

## Demo mode

Set `DEMO_MODE=true` (the Render Blueprint does) for a public portfolio link that needs no sign-in.
At startup the server creates a `demo` account with a random password nobody knows, and
`POST /demo-token` hands a token for it to anyone. The frontend calls that endpoint when there is
no saved session, so visitors land straight on the dashboard. With `DEMO_MODE` unset or false,
`/demo-token` answers 404 and the sign-in page is shown as before.

What to know before leaving it on:

- Every visitor shares one account, so they see each other's saved runs and can delete them.
- Anyone can create simulations, which are stored in the database. Nothing limits how many, so see
  the rate-limiting note below, and keep an eye on the database size on a free plan.
- The `admin` account still works through `/token` and the API docs at `/docs`, but the web page
  no longer shows a sign-in form while demo mode is on.
- A token lasts 60 minutes. When it expires the page signs in again by itself.

## Before putting it on the internet

- Serve it over HTTPS (terminate TLS at the host or a reverse proxy).
- Add rate limiting. Nothing limits sign-in attempts, and `/monte-carlo` is public: it is capped
  per request (3.6 million simulated months) but not per client.
- Plan for schema changes. Tables are created at startup with `create_all`, which does not alter a
  table that already exists, and there is no migration tool. Changing a model means a manual
  migration or a rebuilt database. For example, a database created before
  `ix_simulations_user_created` was added will not get the index on its own.
- Use a managed PostgreSQL with backups, and give the application its own limited database role.
