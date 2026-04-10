# College Management System (CMS) — Powered by Gemma 4

![CMS Architecture Banner](frontend/assets/img/icon.png)

A fully open-source, offline-first College Management System designed to bridge the data-analytics gap in institutions worldwide, powered completely locally by **Google's Gemma 4**.

Submitted for the **Google DeepMind + Kaggle: Gemma 4 Good Hackathon**.

## Overview
Educational administrators waste countless hours manually generating reports spanning attendance, fee defaults, and academic standing. This system provides a 100% offline, privacy-first alternative featuring **AIRA** (Autonomous Intelligent Research Assistant), powered completely by Gemma 4. 

AIRA autonomously fetches SQLite data based on mathematical Role-Based Access Controls (Admin vs. Faculty vs. Student) via Function Calling, generating PDF/Excel reports in milliseconds.

## Features
- 🤖 **Offline Gemma 4 Routing**: Connects to `gemma4:4b` via local Ollama. No cloud APIs, no data leaks.
- 🔒 **Role-Based Context Windows**: The prompt dynamically scopes. Faculty only see *their* students. Admins see *all* students.
- 📊 **Natural Language DB**: "Show me fee defaulters in CS Dept" -> Automatically extracts parameterized JSON, hits SQLite, and builds a UI table.
- 📱 **WhatsApp Automations**: Hooks natively for localized alerting.
- 📄 **1-Click PDF/Excel**: Generate beautiful, formatted reports instantly through AI chat.

## Repository Structure
```
management-system_gemma4/
├── backend/                  # Python Flask Engine + Ollama Wrappers
│   ├── aira/                 # AIRA Agent Routing Modules
│   │   ├── router.py         # Dynamic Role Injector
│   │   └── admin_agent.py    # ...
│   ├── app/                  # Main MVC architecture
│   └── ai_client.py          # Guardrailed Gemma 4 interface
├── frontend/                 # Responsive Vanilla JS/HTML Interface
├── docs/HACKATHON.md         # Technical Rubric Documentation
└── start_server.py           # Universal Boot Wrapper
```

## Setup & Installation
Requires [uv Python manager](https://github.com/astral-sh/uv) and Node.js.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NALIBAK/management-system.git management-system_gemma4
   cd management-system_gemma4
   ```

2. **Start Ollama Locally**:
   Ensure Ollama is running on port 11434 with Gemma 4 installed:
   ```bash
   ollama run gemma3:1b
   # Or for heavier hardware:
   ollama run gemma4:4b
   ```

3. **Install Dependencies & Boot**:
   We provide a universal startup script combining the Python backend, Node.js WhatsApp microservice, and HTTP frontend.
   ```bash
   cd backend
   uv venv
   uv run python ../start_server.py
   ```

4. Open exactly: `http://localhost:8000/login.html` in your browser.

## Tech Stack
- Frontend: HTML5, CSS3, Vanilla ES6 JavaScript (No compilation overhead)
- Backend: Python 3.10+, Flask, SQLite
- AI: Google Gemma 4 via Ollama REST API

## Hackathon Evaluation Guide
Please refer to [docs/HACKATHON.md](docs/HACKATHON.md) for a complete breakdown of how this repository fulfills the 30% Innovation, 30% Impact, 25% Execution, and 15% Accessibility (Offline-first) constraints.

## License
Apache 2.0 Open Source.
