# FocusSync — Realtime Collaborative Pomodoro

FocusSync is a real-time collaborative Pomodoro web application designed for exactly two users. It enables partners to join a private room and share one synchronized Pomodoro timer with real-time controls (start, pause, resume, reset, skip, mode switching, and custom duration settings).

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Architecture](#architecture)
5. [Local Setup & Quick Start](#local-setup--quick-start)
6. [Database Setup & In-Memory Fallback](#database-setup--in-memory-fallback)
7. [Docker & Docker Compose Instructions](#docker--docker-compose-instructions)
8. [API Endpoints & Socket.IO Events](#api-endpoints--socketio-events)
9. [Automated & End-to-End Testing](#automated--end-to-end-testing)
10. [Deployment & Environment Variables](#deployment--environment-variables)
11. [Known Limitations](#known-limitations)

---

## Project Overview

FocusSync provides a shared focus experience for study partners, remote work pairs, and productivity buddies.

### Key Highlights:
- **Strict 2-Person Capacity**: Exactly 2 participants per room. Any 3rd participant attempting to join receives a clear "Room Full" notification.
- **Server-Authoritative Timer**: The server controls master timestamps (`started_at`, `target_end_time`, `duration`, `remaining_seconds`, `completed_sessions`), eliminating clock drift between devices.
- **Client-Side Smooth Rendering**: Clients calculate remaining time locally using server time offset calculations (`server_offset = (server_time * 1000) - Date.now()`), rendering smooth 60fps countdowns and SVG progress animations without spamming 1-second socket events.
- **Instant Synchronization**: Any action (start, pause, reset, skip, mode change, settings save) taken by one user is broadcast instantly to the other participant via Socket.IO.

---

## Features

- **Landing Page**: Modern dark theme with hero explanation, key features list, and tabbed forms for creating or joining a room.
- **Active Room Interface**: Clean, single-branding layout with room code copy pill, real connection status badge, participant cards (with avatar initials and online/offline status dots), SVG timer circle, and session counters.
- **Timer Modes**:
  - **Focus Mode**: Default 25 minutes (Orange accent)
  - **Short Break Mode**: Default 5 minutes (Green accent)
  - **Long Break Mode**: Default 15 minutes (Blue accent)
- **Settings Modal**: Interactive `+` and `-` counters for duration adjustments (Focus 1–60m, Short Break 1–30m, Long Break 1–45m), auto-start transitions toggle, and audio notifications toggle.
- **Invite Modal**: Quick copy button for shareable invite URL (`http://.../room/<code>`) and 6-character room code.

---

## Technology Stack

- **Backend**: Python 3.11+, Flask 3.0+, Flask-SocketIO 5.3+, PyMySQL 1.1+
- **Frontend**: HTML5, Vanilla CSS3 (Custom Dark Theme Design System), Vanilla JavaScript (Modular Architecture), Bootstrap 5, Socket.IO JavaScript Client 4.7+, SVG
- **Database**: MySQL 8 with Thread-Safe In-Memory Fallback
- **Deployment**: Docker & Docker Compose

---

## Architecture

```
FocusSync/
├── app/
│   ├── __init__.py          # Flask application factory & SocketIO setup
│   ├── config.py            # Environment configuration & defaults
│   ├── models/              # Dataclasses (Room, Participant, TimerState, RoomSettings)
│   │   ├── room.py
│   │   ├── participant.py
│   │   ├── timer.py
│   │   └── settings.py
│   ├── repositories/        # Repository pattern (Base, MemoryRepo, MySQLRepo)
│   │   ├── base.py
│   │   ├── memory_repo.py
│   │   └── mysql_repo.py
│   ├── services/            # Core business logic
│   │   ├── room_service.py
│   │   ├── timer_service.py
│   │   ├── presence_service.py
│   │   └── settings_service.py
│   ├── routes/              # HTTP Page & REST API routes
│   │   ├── main_routes.py   # /, /room/<room_code>
│   │   └── api_routes.py    # /api/health, /api/rooms
│   ├── sockets/             # Socket.IO real-time event handlers
│   │   ├── room_events.py
│   │   ├── timer_events.py
│   │   └── presence_events.py
│   ├── utilities/           # Helpers & infrastructure
│   │   ├── db.py            # Database fallback detector & logger
│   │   ├── validators.py    # Username, room code & duration validators
│   │   ├── constants.py     # TimerMode & TimerStatus Enums
│   │   └── logger.py        # Structured logging setup
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Main document layout & CDNs
│   │   ├── index.html       # Landing page (Hero + Create/Join card)
│   │   └── room.html        # Active Room UI (Timer, Participants, Modals)
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
│           ├── room.js
│           ├── modal.js
│           └── notifications.js
├── database/                # MySQL 8 schema & initializer
│   ├── schema.sql
│   └── init_db.py
├── tests/                   # Automated Pytest & E2E test scripts
│   ├── test_models.py
│   ├── test_rooms.py
│   ├── test_timer.py
│   ├── test_routes.py
│   ├── test_sockets.py
│   └── test_e2e_two_browsers.py
├── Dockerfile & docker-compose.yml
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

## Database Setup & In-Memory Fallback

FocusSync supports two database modes:

1. **MySQL 8 (Production / Docker Mode)**:
   - Connects to MySQL using PyMySQL.
   - Initialized using `database/schema.sql`.

2. **In-Memory Fallback (Local Development Mode)**:
   - Activated automatically if MySQL is offline or not installed.
   - Thread-safe dictionary store using `threading.RLock()`.
   - Logs database mode clearly on startup:
     ```
     Database Mode: In-Memory Fallback (Thread-Safe)
     ```

---

## Docker & Docker Compose Instructions

To spin up the application with a dedicated MySQL 8 database container:

```bash
docker compose up --build
```

Services started:
- `web`: Flask-SocketIO app on port `5000`
- `db`: MySQL 8.0 container on port `3306`

---

## API Endpoints & Socket.IO Events

### REST API Endpoints
- `GET /api/health`: Healthcheck & database mode status (`MySQL 8` or `In-Memory Fallback`)
- `POST /api/rooms/create`: Create a new room with username
- `POST /api/rooms/join`: Join an existing room code with username
- `GET /api/rooms/<code>`: Fetch current room state and participant metadata

### Socket.IO Events
- **Client -> Server**:
  - `join_room`, `leave_room`, `request_sync`
  - `timer_start`, `timer_pause`, `timer_resume`, `timer_reset`, `timer_skip`, `timer_change_mode`
  - `settings_updated`
- **Server -> Client / Room Broadcast**:
  - `room_state`, `participant_joined`, `participant_left`, `presence_update`
  - `timer_start`, `timer_pause`, `timer_resume`, `timer_reset`, `timer_skip`, `timer_mode_changed`
  - `settings_updated`, `room_full`, `room_error`

---

## Automated & End-to-End Testing

### 1. Run Unit & Integration Tests (`pytest`)
```bash
python -m pytest -v
```

### 2. Run Real Two-Browser End-to-End Verification Test
Make sure the server is running on `http://localhost:5000`, then run:

```bash
python tests/test_e2e_two_browsers.py
```

Tests performed:
- [OK] Server health check
- [OK] Room creation & socket connection (Browser 1)
- [OK] Room joining (Browser 2)
- [OK] Shared timer controls sync (Start, Pause, Resume, Reset, Skip, Mode Change)
- [OK] Duration settings sync
- [OK] 3rd user room full rejection

---

## Deployment & Environment Variables

Copy `.env.example` to `.env` to configure production environment variables:

```env
PORT=5000
FLASK_DEBUG=False
SECRET_KEY=focussync-secret-key-super-secure-2026

# MySQL Credentials (Optional if using In-Memory Fallback)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=focussync_user
MYSQL_PASSWORD=focussync_password
MYSQL_DB=focussync_db
```

---

## Known Limitations

- Maximum room capacity is strictly capped at **2 participants** by design. Additional participants will be rejected with a `room_full` status message.
