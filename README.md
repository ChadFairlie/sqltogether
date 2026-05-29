<p align="center">
  <!-- Replace this with your own SQLTogether logo when ready -->
  <!-- <img src="docs/assets/sqltogether-logo.png" alt="SQLTogether Logo" width="150"><br> -->

  <strong style="font-size: 24px;">SQLTogether</strong><br>
  <em>A browser-based collaborative SQL learning environment for real-time query editing, teaching, and database practice.</em>
</p>

---

# SQLTogether

SQLTogether is a collaborative browser-based SQL learning and editing platform.

The project is being adapted from [PyTogether](https://github.com/SJRiz/pytogether), originally created by **Syed Jawad Rizvi**. PyTogether was built as a real-time collaborative Python IDE for learning, teaching, and pair programming. SQLTogether keeps the collaborative learning idea, but shifts the focus from Python execution to SQL practice, database exploration, and query-based learning.

> **Project status:** Early adaptation. Some parts of the codebase may still reference Python, Pyodide, or PyTogether while the project is being converted.

---

## Planned Features

- **Real-time SQL Collaboration** - Edit SQL queries together in the same workspace.
- **SQL Editor Support** - CodeMirror-based SQL editing with syntax highlighting.
- **Query Execution** - Run SQL queries against safe learning databases.
- **Result Tables** - View query results in a clean table-based interface.
- **Groups & Projects** - Organize learners, classes, teams, and database exercises.
- **Share Links** - Share SQL projects or query workspaces with others.
- **Live Cursors & Selections** - See collaborators editing in real time.
- **Live Chat and Voice Calls** - Communicate inside project workspaces.
- **Live Drawings** - Annotate or explain database concepts visually.
- **Smart Autosave** - Save project state automatically while users work.

---

## About SQLTogether

Learning SQL is often easier when students can see the database, run queries, compare results, and work through mistakes together.

SQLTogether is designed to be a simple collaborative environment for:

- SQL beginners
- students
- teachers
- tutors
- coding clubs
- database practice sessions
- interview preparation
- pair learning

The goal is not to replace full database administration tools like pgAdmin, DataGrip, DBeaver, or MySQL Workbench. Instead, SQLTogether focuses on a lighter learning-first experience where users can write queries, run them, and collaborate without needing a complex local setup.

> **Note:** SQLTogether is intended for education, practice, and collaborative learning. It is not currently designed as a production database management tool.

---

## Why SQLTogether?

Most SQL tools are built for developers, analysts, or database administrators. They can be powerful, but they are not always beginner-friendly.

SQLTogether aims for:

- **Simple Setup** - Open a browser, join a project, and start writing SQL.
- **Beginner Focus** - Keep the interface focused on queries, tables, and results.
- **Real-Time Learning** - Let teachers, classmates, or mentors work in the same SQL editor.
- **Safe Practice** - Use controlled databases or sandboxed execution for learning.
- **Teaching-Friendly Workspaces** - Keep groups, projects, chat, and collaboration in one place.

---

## Current Technical Direction

SQLTogether is being adapted from the PyTogether codebase.

The inherited stack currently includes:

- **Backend:** Django, Django REST Framework
- **Real-Time:** Y.js, WebSockets, Django Channels
- **Async Processing:** Celery
- **Data Store:** PostgreSQL
- **Caching, Broker, and Channel Layers:** Redis
- **Frontend:** React, Tailwind CSS, CodeMirror
- **Deployment:** Docker-based backend, React frontend, reverse proxy support
- **CI/CD:** GitHub Actions

The SQL-specific execution layer is still being designed.

Possible options include:

- SQLite in the browser
- DuckDB-WASM
- server-side PostgreSQL sandboxes
- disposable per-session database containers
- controlled read-only sample databases

For safety, the first version should avoid running user SQL directly against any production database.

---

## Roadmap

### Phase 1: Rebrand and Clean Import

- Rename PyTogether references to SQLTogether.
- Replace Python-focused README/docs.
- Replace frontend branding.
- Preserve original license and attribution.
- Remove links that make this look like the official PyTogether project.

### Phase 2: SQL Editor Conversion

- Change editor language mode from Python to SQL.
- Add SQL syntax highlighting.
- Add query execution button states.
- Add query result table UI.
- Add error output for invalid SQL.

### Phase 3: SQL Execution Layer

- Decide the first SQL engine.
- Add safe query execution.
- Add query timeouts.
- Add row limits.
- Block or isolate dangerous commands where needed.
- Add sample databases for practice.

### Phase 4: Learning Features

- Add SQL exercises.
- Add starter schemas.
- Add project templates.
- Add teacher/student workflows.
- Add exportable query results.
- Add guided database lessons.

---

## Local Development

### Requirements

- Docker
- Node.js
- npm

### Run Locally

From the project root:

```bash
# 1. Install dependencies
npm install

# 2. Start the development environment
npm run dev
```

The frontend should be available at:

```txt
http://localhost:5173
```

Use `CTRL+C` to stop the development process.

> **Development note:** During the early conversion from PyTogether to SQLTogether, some local setup files, seed users, environment variables, and settings may still use PyTogether naming. These should be cleaned up as part of the rebrand.

---

## Self-Hosting

SQLTogether is intended to support self-hosting, especially for educators, schools, tutors, and private learning groups that want control over their data and learning environment.

The inherited Docker-based self-hosting flow may still require cleanup while the project is being converted.

General flow:

```bash
git clone https://github.com/YOUR_USERNAME/sqltogether.git
cd sqltogether
```

Configure backend environment variables:

```env
PROD=selfhost
DOMAIN=your_ip_address_or_domain
USE_HTTPS=False
```

Configure frontend environment variables:

```env
VITE_DOMAIN="your_ip_address_or_domain"
```

Build the frontend:

```bash
cd frontend/reactapp
npm install
npm run build
```

Start the self-hosted containers:

```bash
cd ../../self-hosting
docker compose up -d --build
```

> **Security note:** SQL execution needs careful sandboxing before public self-hosted use. Do not connect SQLTogether directly to a sensitive production database.

---

## Attribution

SQLTogether is based on [PyTogether](https://github.com/SJRiz/pytogether), created by **Syed Jawad Rizvi**.

PyTogether is a collaborative browser-based Python IDE with real-time editing, live drawing, chat, voice calls, groups, projects, and browser-based Python execution.

This project is an independent adaptation focused on SQL learning and collaborative database practice.

SQLTogether is not the official PyTogether project and is not affiliated with or endorsed by the original PyTogether author unless stated otherwise.

---

## License

This project is based on PyTogether, which is licensed under the MIT License.

The original MIT license notice has been preserved in this repository.

Original work:

```txt
Copyright (c) 2025 Syed Jawad Rizvi
```

Modifications:

```txt
Copyright (c) 2026 SQLTogether contributors
```

See the `LICENSE` file for full license details.
