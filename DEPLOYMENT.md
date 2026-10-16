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
- **`VITE_API_URL`** when the frontend is built, if the API is not at `http://localhost:8000`. It is
  baked into the JavaScript bundle at build time.

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

**Status.** The full image has not been built or run: Docker was not available where this was last
worked on. What was checked is the first stage. Its steps (copy the listed files, `npm ci`,
`npm run build`) were run outside Docker and build successfully; that check found the stage
failing because `tsconfig.node.json` was never copied, which is now fixed. Treat the rest of the
image as a starting point, not a verified deployment.

Because the frontend calls `http://localhost:8000` unless `VITE_API_URL` is set when it is built,
the image as it stands works when you open it on the machine running the container and not from a
remote host.

## Before putting it on the internet

- Serve it over HTTPS (terminate TLS at the host or a reverse proxy).
- Add rate limiting. Nothing limits sign-in attempts, and `/monte-carlo` is public: it is capped
  per request (3.6 million simulated months) but not per client.
- Plan for schema changes. Tables are created at startup with `create_all`, which does not alter a
  table that already exists, and there is no migration tool. Changing a model means a manual
  migration or a rebuilt database. For example, a database created before
  `ix_simulations_user_created` was added will not get the index on its own.
- Use a managed PostgreSQL with backups, and give the application its own limited database role.
