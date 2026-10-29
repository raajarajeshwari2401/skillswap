# ⚡ SkillSwap — College Peer Skill Exchange Platform

SkillSwap is a production-grade, Python-based peer-to-peer educational skill exchange web application built specifically for college students. Students publish skills they can teach (such as Python web development, linear algebra proofs, or Figma UI design) and request help with challenging coursework.

SkillSwap is completely cash-free: learners pay with points earned by tutoring peers, backed by a persistent double-entry ledger, escrow reservation, and an explainable symbolic difficulty scoring engine.

---

## 🏛️ Academic Concepts & Source Code Implementation

This project implements all core computer science academic concepts directly within the Python codebase:

| Academic Concept | Implementation Details | Source Files |
| :--- | :--- | :--- |
| **Object-Oriented Programming (OOP)** | Inheritance, domain encapsulation, state-machine transitions, model relationships (`cascade`, `back_populates`), property methods, and validation. | [`app/models/user.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/models/user.py)<br>[`app/models/skill.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/models/skill.py)<br>[`app/models/wallet.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/models/wallet.py)<br>[`app/models/exchange.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/models/exchange.py)<br>[`app/models/availability.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/models/availability.py)<br>[`app/models/review.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/models/review.py) |
| **Symbolic Mathematics (SymPy)** | Server-side non-arbitrary points calculation. Uses SymPy symbols and mathematical expressions: $\text{Points} = \left(\frac{d}{30}\right) \cdot b \cdot m + \min(5 \cdot (p - 1), 15)$. Exact results: Beginner 30m = 10 pts; Intermediate 60m = 30 pts; Advanced 60m = 40 pts. | [`app/services/scoring_service.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/services/scoring_service.py)<br>[`tests/test_sympy_scoring.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/tests/test_sympy_scoring.py) |
| **Functional Programming** | Pure scoring functions without side effects, immutable mapping, functional filtering, lambda keys for multidimensional sorting, and list/dictionary comprehensions. | [`app/services/matching_service.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/services/matching_service.py)<br>[`tests/test_functional_matching.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/tests/test_functional_matching.py) |
| **Python Multiprocessing** | CPU-bound parallel batch matching engine utilizing `concurrent.futures.ProcessPoolExecutor` and worker process chunks. Tracks worker process IDs (`pid`) to verify execution. Safely avoids sharing mutable database state across processes. | [`matching/multiprocessing_matcher.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/matching/multiprocessing_matcher.py)<br>[`tests/test_multiprocessing.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/tests/test_multiprocessing.py) |
| **Raw TCP Socket Programming** | Multi-threaded client-server architecture using Python's standard `socket` and `threading` libraries. Implements structured newline-delimited JSON protocol, connection timeouts, authentication tokens, and administrative health queries. | [`app/sockets/raw_tcp_server.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/sockets/raw_tcp_server.py)<br>[`app/sockets/raw_tcp_client.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/sockets/raw_tcp_client.py)<br>[`tests/test_raw_socket.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/tests/test_raw_socket.py) |
| **Real-Time WebSockets** | Flask-SocketIO event gateway delivering instant browser toast notifications to private authenticated rooms (`user_<id>`) when sessions are requested, accepted, scheduled, completed, or reviewed. | [`app/sockets/events.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/sockets/events.py)<br>[`app/services/notification_service.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/services/notification_service.py)<br>[`app/static/js/main.js`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/static/js/main.js) |
| **Database Architecture (ACID)** | Double-entry transaction ledger, row-level concurrency protection (`with_for_update`), escrow reservation, unique idempotency keys, foreign keys, unique constraints, and persistent PostgreSQL/SQLite support. | [`app/models/wallet.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/models/wallet.py)<br>[`app/services/wallet_service.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/app/services/wallet_service.py)<br>[`tests/test_wallet_transactions.py`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/tests/test_wallet_transactions.py) |

---

## 📁 Project Directory Structure

```text
skillswap/
├── app/
│   ├── __init__.py               # Flask application factory, SocketIO, Login, CSRF
│   ├── extensions.py             # SQLAlchemy, LoginManager, SocketIO, Migrate
│   ├── models/                   # OOP SQLAlchemy domain models
│   │   ├── __init__.py
│   │   ├── user.py               # User, profile, reputation
│   │   ├── skill.py              # SkillCategory, SkillOffer, SkillRequest
│   │   ├── exchange.py           # State machine lifecycle
│   │   ├── wallet.py             # Wallet & immutable PointTransaction ledger
│   │   ├── availability.py       # AvailabilitySlot calendar scheduling
│   │   ├── review.py             # 1-5 Star verified feedback
│   │   ├── notification.py       # Persistent user notifications
│   │   ├── report.py             # Dispute & report moderation
│   │   └── audit.py              # System security audit log
│   ├── routes/                   # Flask view controllers
│   │   ├── __init__.py
│   │   ├── main.py               # Landing page, dashboard, help
│   │   ├── auth.py               # Registration, login, session
│   │   ├── skills.py             # Explore, create, edit, search
│   │   ├── exchanges.py          # Request, accept, schedule, settle, cancel
│   │   ├── matching.py           # Compatibility recommendations & SymPy preview API
│   │   ├── wallet.py             # Wallet balance & transaction history
│   │   ├── notifications.py      # Notification center
│   │   ├── profile.py            # Public profiles & availability slots
│   │   ├── reviews.py            # Post-exchange reviews
│   │   └── admin.py              # Moderation, disputes & audit ledger
│   ├── services/                 # Core business & academic services
│   │   ├── __init__.py
│   │   ├── scoring_service.py    # SymPy symbolic formula engine
│   │   ├── matching_service.py   # Functional programming pipeline (map/filter/sorted)
│   │   ├── wallet_service.py     # ACID wallet, escrow, & idempotency controls
│   │   └── notification_service.py # DB persistence & Socket.IO emitter
│   ├── sockets/                  # Real-time WebSockets & Raw TCP sockets
│   │   ├── __init__.py
│   │   ├── events.py             # Flask-SocketIO event handlers
│   │   ├── raw_tcp_server.py     # Standalone Python socket TCP server
│   │   └── raw_tcp_client.py     # Python socket TCP client with timeouts
│   ├── static/
│   │   ├── css/main.css          # Ultra-modern responsive styling
│   │   └── js/main.js            # Socket.IO client & live point calculator
│   └── templates/                # 16 complete Jinja2 HTML templates
│       ├── base.html
│       ├── index.html            # Landing page with DB stats & SymPy explainer
│       ├── dashboard.html        # Student dashboard
│       ├── help.html             # Platform rules & FAQ
│       ├── auth/                 # Login & Register with 50-pt welcome grant
│       ├── skills/               # Explore, details, create offer, create request
│       ├── matching/             # AI recommendations & score breakdown
│       ├── exchanges/            # Sessions list & state-machine detail
│       ├── wallet/               # Balance cards & transaction table
│       ├── notifications/        # Notification center
│       ├── profile/              # Public profile, edit settings, availability
│       ├── reviews/              # 1-5 Star feedback
│       ├── admin/                # Admin dashboard & moderation
│       └── errors/               # 404 & 500 error handlers
├── matching/
│   ├── __init__.py
│   └── multiprocessing_matcher.py # Parallel batch matching using multiprocessing
├── tests/
│   ├── conftest.py               # In-memory SQLite & mock user fixtures
│   ├── test_sympy_scoring.py     # SymPy formulas & examples tests
│   ├── test_auth.py              # Registration, hashing, sessions tests
│   ├── test_wallet_transactions.py # Idempotency, escrow, double-spend tests
│   ├── test_functional_matching.py # Pure functions, filter, map, sorted tests
│   ├── test_multiprocessing.py   # ProcessPoolExecutor tests
│   ├── test_raw_socket.py        # Raw TCP client-server tests
│   └── test_e2e_workflow.py      # Complete 10-step integration test
├── config.py                     # Dev, Testing, & Production configs
├── run.py                        # Local dev server (Socket.IO + Raw TCP)
├── wsgi.py                       # Cloud production WSGI entrypoint
├── init_db.py                    # Database creation & initial demo seed script
├── requirements.txt              # Pinned Python package dependencies
├── .env.example                  # Environment variables template
├── .gitignore
├── Procfile                      # Gunicorn + Eventlet WSGI runner
└── render.yaml                   # Render Blueprint for Web + PostgreSQL
```

---

## 💻 Step-by-Step Local Setup Instructions (Windows & VS Code)

Follow these exact steps to run SkillSwap locally on Windows using VS Code without requiring paid cloud hosting:

### 1. Open Project in VS Code
Open VS Code, press `Ctrl + O` (or `File -> Open Folder...`), and select the folder:
`C:\Users\Swedha Surya\.gemini\antigravity\scratch\skillswap`

### 2. Open PowerShell Terminal in VS Code
Press `` Ctrl + ` `` to open the integrated terminal in VS Code.

### 3. Create and Activate a Python Virtual Environment
Run the following PowerShell commands:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first).*

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Setup Environment File
Copy the provided `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
By default, `.env` is configured with `DATABASE_URL=sqlite:///skillswap.db` for instantaneous local execution with zero setup.

### 6. Initialize & Seed Database
Execute the database initialization script:
```powershell
python init_db.py
```
This automatically:
- Creates all tables.
- Seeds academic categories (Computer Science, Mathematics, Languages, Design, Music, Business).
- Configures default demo student accounts (`maya@skillswap.edu`, `ethan@skillswap.edu`, `sophia@skillswap.edu`, password `Password123!`).
- Calculates and provisions initial skill listings using SymPy.
- Securely creates the initial Administrator account (`admin@skillswap.edu`, password `AdminSecurePass2026!`).

### 7. Run the Application
```powershell
python run.py
```
Output:
```text
[*] Starting Raw TCP Socket Server on 127.0.0.1:9099...
[*] Starting SkillSwap Web Application on http://127.0.0.1:5000...
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🧪 Running the Pytest Test Suite

Execute the comprehensive test suite verifying all academic concepts, unit calculations, and the end-to-end 10-step lifecycle:

```powershell
pytest -v
```

To run a specific test module:
```powershell
# Run SymPy scoring verification
pytest tests/test_sympy_scoring.py -v

# Run the 10-step E2E lifecycle test
pytest tests/test_e2e_workflow.py -v

# Run raw TCP socket test
pytest tests/test_raw_socket.py -v

# Run multiprocessing test
pytest tests/test_multiprocessing.py -v
```

---

## 🌐 Cloud Deployment Guide (Persistent PostgreSQL + WebSockets)

SkillSwap is pre-configured for automated deployment to cloud providers supporting Python, PostgreSQL, and WebSockets (e.g. Render, Railway, Heroku).

### Deploying to Render.com (Recommended Blueprint)
1. Push your repository to GitHub.
2. Sign in to [Render](https://render.com).
3. Click **New +** -> **Blueprint**.
4. Select your `skillswap` GitHub repository. Render will automatically detect [`render.yaml`](file:///C:/Users/Swedha%20Surya/.gemini/antigravity/scratch/skillswap/render.yaml):
   - Provisions a persistent **PostgreSQL** instance (`skillswap-db`).
   - Automatically injects the `DATABASE_URL` environment variable.
   - Deploys the web service using `gunicorn --worker-class eventlet -w 1 wsgi:app`.
5. Once deployed, run `python init_db.py` in the Render Shell tab to seed initial categories.

### Production Environment Variables
| Variable | Description | Recommended Setting |
| :--- | :--- | :--- |
| `FLASK_ENV` | Environment identifier | `production` |
| `SECRET_KEY` | Cryptographic session key | 64-char random hex string |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SOCKETIO_ASYNC_MODE` | WebSocket async worker engine | `eventlet` |
| `SESSION_COOKIE_SECURE` | HTTPS-only cookies | `True` |
| `ADMIN_EMAIL` | Initial admin email | `admin@yourcollege.edu` |
| `ADMIN_PASSWORD` | Initial admin password | Strong random passphrase |

---

## 🔒 Security Architecture
- **Password Protection**: Passwords hashed with Werkzeug's PBKDF2/SHA-256 algorithm.
- **CSRF Protection**: All forms guarded with `Flask-WTF` CSRF tokens.
- **Database Safety**: Parameterized queries via SQLAlchemy ORM; prevent SQL injection.
- **Row Locking**: Critical escrow settlements use `with_for_update()` to eliminate race conditions and double-spending.
- **Privacy Awareness**: Only generalized locations (e.g. "North Science Quad") are shown publicly; private emails/coordinates are never exposed.
