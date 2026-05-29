# SQLTogether Phase 0 findings — Stabilize Imported Codebase

This document summarizes our findings and verification results for Phase 0: "Stabilize imported codebase".

---

## 1. Environment & Setup Verification

The development environment was successfully initialized and started using the following steps:
1. **Node Dependencies**: `npm install` at the project root installed all workspace dependencies and post-installed the React + Vite frontend packages in `frontend/reactapp/` without issues.
2. **Local Servers**:
   - **Frontend**: The Vite development server was started successfully on `http://localhost:5173` via `npm run dev --prefix frontend/reactapp`.
   - **Backend**: Built and started the dev stack containers using the host's `docker.exe compose -f docker-compose-dev.yaml up --build`.

---

## 2. Docker Service Roles

The following Docker services are configured in `docker-compose-dev.yaml` and were verified as fully functional:

| Service Name | Docker Image / Context | Purpose | Verification Status |
|---|---|---|---|
| **django-builder** | `pytogether-backend:latest` (built from `./backend`) | Acts as the parent image builder containing Python, system libraries, and requirements. | Builds successfully. |
| **django-init** | `pytogether-backend:latest` | Runs database migrations and seeds default admin users (`test1@gmail.com` and `test2@gmail.com` with password `testtest`). Exits cleanly. | Executed successfully; migrations applied. |
| **django** | `pytogether-backend:latest` | Runs the Django ASGI dev server on `http://0.0.0.0:8000` via `daphne` ASGI/Daphne. Handles API endpoints and WebSocket consumers. | Active on `localhost:8000`. |
| **db** | `postgres:15` | The application database, storing metadata: user credentials, groups, project information, and persisted Y.js document states. | Running and accepting connections. |
| **redis** | `redis:7-alpine` | Used as the Django Channels channel layer broker, the Celery message broker, and the Y.js in-memory sync document cache. | Active on port `6379`. |
| **celery** | `pytogether-backend:latest` | Celery asynchronous worker that handles periodic persistence tasks and ghost project cleanup. | Active; worker connected to Redis. |
| **celery-beat** | `pytogether-backend:latest` | Celery periodic scheduler that sends task heartbeats to Celery. | Active; scheduler triggering tasks. |

---

## 3. Environment Variables (.env.dev)

The backend uses `./backend/.env.dev` to configure settings in development:

- `DJANGO_SECRET_KEY`: Cryptographic signing key for Django (sessions, signed URLs, share tokens).
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` / `POSTGRES_HOST` / `POSTGRES_PORT`: Connection parameters for the PostgreSQL metadata database.
- `DATABASE_URL`: DB connection URI used by `dj-database-url` to parse database connection settings.
- `REDIS_HOST` / `REDIS_PORT`: Connection settings for the Redis caching and Channel Layer broker.
- `PROD`: Set to `development` to dictate configuration paths.
- `DOMAIN`: Set to `localhost:5173` (used for generating absolute frontend redirection and sharing links).
- `USE_HTTPS`: Set to `False` in local development.

---

## 4. Feature Verification

Key collaborative features were verified using custom API and WebSocket automation test suites:

- **Authentication & User Flows**:
  - API `POST /api/auth/token/` returns JWT access and refresh tokens for users `test1@gmail.com` and `test2@gmail.com` successfully.
- **Groups & Projects**:
  - API `POST /groups/create/` successfully creates groups with access codes (e.g. `kOnA2K4LB9Hh`).
  - API `PUT /groups/join/` allows second users to successfully join groups using the access code.
  - API `POST /groups/{gid}/projects/create/` successfully registers and initializes project workspaces.
- **WebSocket & Real-Time Sync**:
  - WebSocket connection to `ws://localhost:8000/ws/groups/{gid}/projects/{pid}/code/?token={token}` handshakes successfully via `JWTAuthMiddleware`.
  - The server transmits the initial Y.js document sync payload (`"type": "sync"`) containing binary-encoded `ydoc_b64` state.
  - Chat messages are successfully sent from clients and broadcast to all project room participants via Redis channel layers (`"type": "chat_message"`).
- **Autosave & Persistence**:
  - Celery periodic worker logs verify that `snapshot_dirty_projects` and `cleanup_ghost_projects` tasks are executing successfully every 30 seconds to persist modified Y.js states from Redis to Postgres.

---

## 5. Issues & Notes Discovered

1. **Host Docker Command vs WSL**:
   - In environments where WSL 2 is installed but the native `docker` CLI package isn't enabled within the distribution (or is handled via Docker Desktop Integration), running the root script `npm run dev` as-is will fail because it tries to call local `docker compose`.
   - **Workaround**: We started the Vite server locally using `npm run dev --prefix frontend/reactapp` and orchestrated the containers via the Windows-accessible host client `docker.exe compose -f docker-compose-dev.yaml up --build`. This starts the environment seamlessly.
2. **Attribution & Licenses**:
   - The license attribution is fully intact: the original MIT copyright notice from Syed Jawad Rizvi (`Copyright (c) 2025 Syed Jawad Rizvi`) has been preserved in the `LICENSE` file. A secondary copyright block has been added for `SQLTogether contributors` as required by Phase 0 attribution guidelines.
