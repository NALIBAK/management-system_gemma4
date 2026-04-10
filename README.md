# College Management System (CMS) — Powered by Gemma 4



A fully open-source, offline-first College Management System designed to bridge the data-analytics gap in institutions worldwide, powered completely locally by **Google's Gemma 4**.

Submitted for the **Google DeepMind + Kaggle: Gemma 4 Good Hackathon**.

## Overview
Educational administrators waste countless hours manually generating reports spanning attendance, fee defaults, and academic standing. This system provides a 100% offline, privacy-first alternative featuring **AIRA** (Autonomous Intelligent Research Assistant), powered completely by Gemma 4. 

AIRA autonomously fetches MySQL data based on mathematical Role-Based Access Controls (Admin vs. Faculty vs. Student) via Function Calling, generating PDF/Excel reports in milliseconds.

## Features
- 🤖 **Offline Gemma 4 Routing**: Connects to `gemma4:e4b` via local Ollama. No cloud APIs, no data leaks.
- 🔒 **Role-Based Context Windows**: The prompt dynamically scopes. Faculty only see *their* students. Admins see *all* students.
- 📊 **Natural Language DB**: "Show me fee defaulters in CS Dept" -> Automatically extracts parameterized JSON, hits XAMPP MySQL, and builds a UI table.
- 📱 **WhatsApp Automations**: Hooks natively for localized alerting.
- 📄 **1-Click PDF/Excel**: Generate beautiful, formatted reports instantly through AI chat.

## Repository Structure

```
management-system_gemma4/
├── backend/                       # Python Flask API Engine
│   ├── app/                       # Main MVC Architecture
│   │   ├── routes/                # API Endpoints
│   │   │   ├── aira.py            # AI Chatbot/Reports logic
│   │   │   ├── auth.py            # JWT Authentication
│   │   │   ├── notifications.py   # System notifications
│   │   │   └── whatsapp.py        # WhatsApp service hook
│   │   ├── report_templates/      # Jinja2/WeasyPrint Templates
│   │   │   └── fee_defaulters.html
│   │   ├── utils/
│   │   │   └── auth.py            # Security & Scope wrappers
│   │   └── db.py                  # PyMySQL DB connector
│   ├── reports/                   # Generated reports output dir
│   ├── database/                  # SQL Schemas
│   │   ├── schema.sql             # Table creation logic
│   │   └── seed.sql               # Base system seeds
│   ├── tests/                     # System End-to-End tests
│   │   └── system_test.py
│   ├── ai_client.py               # Gemma 4 Ollama HTTP integration
│   ├── config.py                  # Global App Configuration
│   ├── requirements.txt           # Python backend dependencies
│   ├── run.py                     # Flask WSGI Server Entry Point
│   └── *.py                       # Various debugging/test scripts (repro_staff.py, etc.)
├── frontend/                      # Pure Vanilla HTML5 Dashboard
│   ├── assets/
│   │   ├── css/                   # Global style sheets
│   │   └── js/                    # UI Controllers
│   │       ├── aira.js            # AIRA Chatbot frontend logic
│   │       ├── api.js             # Dedicated API Request wrapper
│   │       └── *.js               # Specific module controllers
│   ├── settings/                  # Application configuration screens
│   └── *.html                     # Views (login, dashboard, students, etc.)
├── whatsapp_service/              # Node.js Alerting Microservice
│   ├── index.js                   # Express + whatsapp-web.js logic
│   └── package.json               # Node dependencies
├── scripts/                       # Local DB Utilities
│   ├── populate_db.py             # Generates 1500+ records and Master accounts
│   ├── reset_admin.py             # Failsafe hash reset
│   └── seed_data.py               # Testing seed scripts
├── docs/
│   └── HACKATHON.md               # 100% Offline / Gemma 4 Evaluation specs
├── .env.example                   # Environment skeleton
├── .gitignore
├── LICENSE                        # Apache 2.0 License
├── README.md                      # Primary Documentation
├── setup_project.py               # Auto-Initialization Auto-Scaffolder
└── start_server.py                # Universal Orchestrator (Boot script)
```

## Setup & Installation
Requires [uv Python manager](https://github.com/astral-sh/uv), Node.js, and **XAMPP (MySQL)**.

> [!WARNING]
> If you are testing the **PDF Generation** feature on Windows, you must install the **GTK3** runtime environment. (Linux/macOS typically have this native).

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NALIBAK/management-system.git management-system_gemma4
   cd management-system_gemma4
   ```

2. **Start Ollama Locally**:
   Ensure Ollama is running on port 11434 with Gemma 4 installed:
   ```bash
   ollama run gemma4:e4b
   ```

3. **Initialize Database (Crucial First Step)**:
   Ensure **XAMPP MySQL** is running on port `3306`. Run the auto-setup script which builds the schemas and injects dummy students/staff into the local MySQL instance automatically.
   ```bash
   uv run python setup_project.py
   ```

4. **Boot the System**:
   Start the centralized orchestrator script which boots the Python backend, frontend HTTP client, and Node WhatsApp service.
   ```bash
   cd backend
   uv venv
   uv run python ../start_server.py
   ```

5. Open exactly: `http://localhost:9000/login.html` in your browser.
   - **Username**: `superadmin`
   - **Password**: `Admin@123`

## Tech Stack
- Frontend: HTML5, CSS3, Vanilla ES6 JavaScript (No compilation overhead)
- Backend: Python 3.10+, Flask, PyMySQL (XAMPP target)
- AI: Google Gemma 4 via Ollama REST API

## Hackathon Evaluation Guide
Please refer to [docs/HACKATHON.md](docs/HACKATHON.md) for a complete breakdown of how this repository fulfills the 30% Innovation, 30% Impact, 25% Execution, and 15% Accessibility (Offline-first) constraints.

## License
Apache 2.0 Open Source.
