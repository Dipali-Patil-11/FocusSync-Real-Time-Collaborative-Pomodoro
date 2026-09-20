# FocusSync — Real-Time Collaborative Pomodoro Session

A real-time collaborative Pomodoro timer that helps two people focus together and stay synchronized.

## 🌐 Live Demo

**[🚀 Open FocusSync](https://focussync-real-time-collaborative.onrender.com/)** — Click here to explore the web app.

FocusSync is a real-time collaborative Pomodoro web application built for exactly two users. It allows two participants on different devices/networks to join a dedicated session and share one synchronized Pomodoro timer with instant controls (start, pause, resume, reset, skip, mode switching, custom duration settings, visual toast notifications, and synthesized sound tones).

- **GitHub Repository**: [https://github.com/Dipali-Patil-11/FocusSync-Real-Time-Collaborative-Pomodoro.git](https://github.com/Dipali-Patil-11/FocusSync-Real-Time-Collaborative-Pomodoro.git)

---

## Table of Contents
1. [Project Overview & Key Highlights](#project-overview--key-highlights)
2. [Terminology & Naming Standard](#terminology--naming-standard)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [Architecture](#architecture)
6. [Local Setup & Quick Start](#local-setup--quick-start)
7. [Real-Time Notifications & Sound System](#real-time-notifications--sound-system)
8. [Database Setup & In-Memory Fallback](#database-setup--in-memory-fallback)
9. [Cloud & Render Deployment](#cloud--render-deployment)
10. [Docker & Container Instructions](#docker--container-instructions)
11. [API Endpoints & Socket.IO Events](#api-endpoints--socketio-events)
12. [Automated & End-to-End Testing](#automated--end-to-end-testing)
13. [Environment Variables](#environment-variables)
14. [Known Limitations](#known-limitations)

---

## Project Overview & Key Highlights

FocusSync provides a shared, accountable focus environment for study collaborators, pair programmers, and remote teammates.

- **Strict 2-Participant Capacity**: Exactly 2 participants per session. Any 3rd participant attempting to join receives a clear "Session Capacity Reached" notification.
- **Server-Authoritative Timer**: The server controls master timestamps (`started_at`, `target_end_time`, `duration`, `remaining_seconds`, `completed_sessions`), eliminating clock drift between devices.
- **Client-Side Smooth Rendering**: Clients calculate remaining time locally using server time offset calculations (`server_offset = (server_time * 1000) - Date.now()`), rendering smooth 60fps countdowns and SVG progress animations without spamming 1-second socket events.
- **Instant Synchronization**: Any action (start, pause, reset, skip, mode change, settings save) taken by one participant is broadcast instantly to the other participant via Socket.IO.
- **Dynamic Origin Invites**: Share links and WebSockets use `window.location.origin` dynamically over HTTPS/HTTP without hardcoded `localhost` dependencies.

---

## Terminology & Naming Standard

The project uses consistent, professional terminology across user interface text, file names, backend services, database models, and socket payload events:

| Concept | Primary Term | Description / Examples |
| :--- | :--- | :--- |
| **Workspace Unit** | **Session** | Replaces old "Room" concept (`SessionService`, `/session/<code>`, `SessionManager`, `session.html`) |
| **User** | **Participant** | People connected to a shared focus session (Max 2 per session) |
| **Session Type** | **Dedicated Session** | Controlled-access 2-person shared focus environment |
| **Identifier** | **Session Code** | 6-character alphanumeric code used for joining (`session_code`) |
| **Share Action** | **Invite to Session** | Share link & copy code actions |
| **Limit Warning** | **Session Capacity Reached** | Replaces old "Room Full" notification when session capacity is reached |

---

## Features

- **Landing Page**: Modern dark theme with hero explanation, key features list, and tabbed forms for creating or joining a session.
- **Active Session Interface**: Clean layout with session code copy pill, real connection status badge, participant cards (with avatar initials and online/offline status dots), SVG timer circle, and session counters.
- **Timer Modes**:
  - **Focus Mode**: Default 25 minutes (Orange accent `#FF6B00`)
  - **Short Break Mode**: Default 5 minutes (Green accent `#22C55E`)
  - **Long Break Mode**: Default 15 minutes (Blue accent `#38BDF8`)
- **Real-Time Notifications & Sound Tones**: Visual toast notifications and synthesized Web Audio API sound tones for session start, completion, participant join, and participant leave.
- **Settings Modal**: Interactive duration adjustments (Focus 1–60m, Short Break 1–30m, Long Break 1–45m), auto-start transitions toggle, and per-user sound notifications toggle.
- **Invite Modal**: Quick copy button for shareable invite URL (`https://.../session/<code>`) and 6-character session code.

---

## Technology Stack

- **Backend**: Python 3.11+, Flask 3.0+, Flask-SocketIO 5.3+, Psycopg 3 (`psycopg[binary]` 3.1+)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Dark Theme Design System), Vanilla JavaScript (Modular Architecture), Bootstrap 5, Socket.IO JavaScript Client 4.7+, SVG Ring
- **Database**: Supabase PostgreSQL (PostgreSQL 15+) with Thread-Safe In-Memory Fallback
- **Deployment**: Render Web Service, Supabase PostgreSQL, Docker

---

## Architecture

```
FocusSync/
├── app/
│   ├── __init__.py          # Flask application factory & SocketIO setup
│   ├── config.py            # Environment configuration & defaults
│   ├── models/              # Dataclasses (Session, Participant, TimerState, SessionSettings)
│   │   ├── session.py
│   │   ├── participant.py
│   │   ├── timer.py
│   │   └── settings.py
│   ├── repositories/        # Repository pattern (Base, MemoryRepo, PostgresRepo)
│   │   ├── base.py
│   │   ├── memory_repo.py
│   │   ├── postgres_repo.py # PostgreSQL / Supabase repository implementation
│   │   └── mysql_repo.py    # Backwards-compatible alias to PostgresRepository
│   ├── services/            # Core business logic
│   │   ├── session_service.py
│   │   ├── timer_service.py
│   │   ├── presence_service.py
│   │   └── settings_service.py
│   ├── routes/              # HTTP Page & REST API routes
│   │   ├── main_routes.py   # /, /session/<session_code>
│   │   └── api_routes.py    # /api/health, /api/sessions
│   ├── sockets/             # Socket.IO real-time event handlers
│   │   ├── session_events.py
│   │   ├── timer_events.py
│   │   └── presence_events.py
│   ├── utilities/           # Helpers & infrastructure
│   │   ├── db.py            # Database mode detector & logger
│   │   ├── validators.py    # Username, session code & duration validators
│   │   ├── constants.py     # TimerMode & TimerStatus Enums
│   │   └── logger.py        # Structured logging setup
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Main document layout & CDNs
│   │   ├── index.html       # Landing page (Hero + Create/Join card)
│   │   └── session.html     # Active Session UI (Timer, Participants, Modals)
│   └── static/
│       ├── css/             # Vanilla CSS design system
│       │   ├── style.css
│       │   ├── components.css
│       │   └── responsive.css
│       └── js/              # Modular Vanilla JS scripts
│           ├── main.js
│           ├── api.js
│           ├── socket.js
│           ├── timer.js
│           ├── session.js
│           ├── modal.js
│           └── notifications.js
├── database/                # PostgreSQL / Supabase schema & initializer
│   ├── schema.sql
│   └── init_db.py
├── tests/                   # Automated Pytest & E2E test scripts
│   ├── test_models.py
│   ├── test_sessions.py
│   ├── test_timer.py
│   ├── test_routes.py
│   ├── test_sockets.py
│   ├── test_postgres_persistence.py
│   └── test_e2e_two_browsers.py
├── Dockerfile & docker-compose.yml
├── Procfile & render.yaml
├── requirements.txt & run.py
├── .env.example & .gitignore
└── README.md
```

---

## Local Setup & Quick Start

### 1. Prerequisites
- Python 3.10+ installed

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python run.py
```

### 4. Open in Browser
- **Application URL**: `http://localhost:5000`
- **Healthcheck Endpoint**: `http://localhost:5000/api/health`

---

## Real-Time Notifications & Sound System

FocusSync includes a real-time notification engine with Web Audio API sound synthesis:

- **Server-Authoritative Events**:
  - `timer_started_notification`: Sent when Focus, Short Break, or Long Break starts.
  - `timer_completed_notification`: Sent when a timer finishes.
  - `participant_joined`: Sent to session (`include_self=False`) when User 2 joins (`"[USERNAME] joined the focus session"`).
  - `participant_left`: Sent to remaining participant when a participant leaves (`"[USERNAME] left the focus session"`).
- **Audio Synthesis**: Web Audio API generates double rising chimes, ascending notes, and soft pings without relying on external MP3 URLs.
- **Autoplay Handling**: Unlocks `AudioContext` automatically on the user's first interaction.
- **Event Deduplication**: Clients track `event_id`s in a Set to guarantee each notification is rendered exactly once.
- **Per-User Sound Preference**: Sound toggle setting operates per user browser locally.

---

## Database Setup & In-Memory Fallback

FocusSync supports two database modes:

1. **PostgreSQL / Supabase (Production Mode)**:
   - Connects using `psycopg3` (`psycopg[binary]`).
   - Tables (`sessions`, `participants`, `timers`, `settings`) initialized safely via `database/init_db.py` using `database/schema.sql`.
   - Requires `DATABASE_SSLMODE=require` for Supabase connections.
   - **Production Safety Guarantee**: If `DATABASE_HOST` is specified when `FLASK_DEBUG=False`, connection failures will log a critical error and throw an exception to prevent silent data loss.

2. **In-Memory Fallback (Local Development Mode)**:
   - Activated automatically when `DATABASE_HOST` is omitted or empty in local development mode (`FLASK_DEBUG=True`).
   - Thread-safe dictionary store using `threading.RLock()`.
   - Logs database mode clearly on startup:
     ```
     Database Mode: In-Memory Fallback (Thread-Safe)
     ```

---

## Cloud & Render Deployment

FocusSync is pre-configured for public deployment on Render and Supabase PostgreSQL:

### Deploying on Render + Supabase:
1. Create a PostgreSQL Database project on [Supabase](https://supabase.com).
2. Note your Supabase connection parameters (Host, Database, User, Password, Port 5432).
3. Create a **Render Web Service** connected to repository `https://github.com/Dipali-Patil-11/FocusSync-Real-Time-Collaborative-Pomodoro.git`.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python run.py`
6. Health Check Path: `/api/health`
7. Configure Environment Variables in Render:
   - `DATABASE_HOST`: `<your-supabase-db-host>`
   - `DATABASE_PORT`: `5432`
   - `DATABASE_USER`: `postgres`
   - `DATABASE_PASSWORD`: `<your-supabase-db-password>`
   - `DATABASE_NAME`: `postgres`
   - `DATABASE_SSLMODE`: `require`
   - `SECRET_KEY`: `<your-random-secret-key>`
   - `SOCKETIO_CORS_ORIGINS`: `*` (or your Render service domain)

The repository includes `render.yaml` for blueprint deployments and `Procfile` for platform execution.

---

## Docker & Container Instructions

To build and run the web application container locally:

```bash
docker compose up --build
```

Services started:
- `web`: Flask-SocketIO app on port `5000`

---

## API Endpoints & Socket.IO Events

### REST API Endpoints
- `GET /api/health`: Healthcheck & database status (`Supabase PostgreSQL` or `In-Memory Fallback`)
- `POST /api/sessions/create`: Create a new session with username
- `POST /api/sessions/join`: Join an existing session code with username
- `GET /api/sessions/<code>`: Fetch current session state and participant metadata

### Socket.IO Events
- **Client -> Server**: `join_session`, `leave_session`, `request_sync`, `timer_start`, `timer_pause`, `timer_resume`, `timer_reset`, `timer_skip`, `timer_change_mode`, `settings_updated`
- **Server -> Client / Session Broadcast**: `session_state`, `participant_joined`, `participant_left`, `presence_update`, `timer_start`, `timer_pause`, `timer_resume`, `timer_reset`, `timer_skip`, `timer_mode_changed`, `timer_started_notification`, `timer_completed_notification`, `settings_updated`, `session_capacity_reached`, `session_error`

---

## Automated & End-to-End Testing

### 1. Run Unit & Integration Tests (`pytest`)
```bash
python -m pytest -v
```

### 2. Run Real Two-Browser End-to-End Test
Ensure the server is running on `http://localhost:5000`, then run:

```bash
python tests/test_e2e_two_browsers.py
```

Tests verified:
- [OK] Server health check
- [OK] Session creation & socket connection (Browser 1)
- [OK] Session joining & self-exclusion (Browser 2)
- [OK] Focus, Short Break, and Long Break start notifications
- [OK] Timer completion notification
- [OK] Leave notification
- [OK] 3rd user session capacity reached rejection

---

## Environment Variables

Copy `.env.example` to `.env` to configure environment parameters:

```env
PORT=5000
FLASK_DEBUG=False
SECRET_KEY=focussync-secret-key-super-secure-2026
SOCKETIO_CORS_ORIGINS=*

# PostgreSQL / Supabase Database Configuration
DATABASE_HOST=aws-0-us-east-1.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_USER=postgres.projectref
DATABASE_PASSWORD=your_supabase_password
DATABASE_NAME=postgres
DATABASE_SSLMODE=require
```

---

## Known Limitations

- Maximum session capacity is strictly capped at **2 participants** by design. Additional participants will be rejected with a `session_capacity_reached` status message.
