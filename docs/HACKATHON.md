# Gemma 4 Good Hackathon — Technical Execution & Rubric Overview

Welcome, Judges! This document maps our project execution directly to the Gemma 4 Good grading rubrics.

---

## 1. Innovation (30%)

Our College Management System completely reimagines institutional data access by integrating Gemma 4 as a persistent, **locally-hosted cognitive agent** named AIRA (Autonomous Intelligent Research Assistant).

### 1.1 Two-Shot Tool-Calling Architecture (Better Than RAG)
Unlike RAG-based systems that retrieve static document chunks, AIRA uses **native Gemma 4 Function Calling** to talk directly to a live MySQL database:

1. **First LLM Call** — Gemma 4 parses the user's natural language query and issues a structured JSON tool call (e.g., `get_low_attendance`, `get_fee_defaulters`, `generate_beautiful_pdf_report`).
2. **Tool Execution** — Our Python backend executes the tool against live MySQL, returning real-time parameterized data.
3. **Second LLM Call (Synthesis)** — The raw tool results are fed back to Gemma 4 to synthesize a clean, markdown-formatted, insight-driven response.

This means every answer reflects the **current state of the database**, not stale cached documents.

### 1.2 Mathematical Role-Based Context Windows
Most LLM deployments use a single system prompt. Our architecture mathematically evaluates the user's role and dynamically scopes the DB context injected into the prompt:
- A **Super Admin** asks "Show top students" → receives the entire college's CGPA ranking.
- A **Faculty Member** asks the exact same prompt → their DB context snapshot only contains students from their assigned sections. Gemma 4 cannot see or infer data outside this scope.
- A **Student** asks about attendance → only their own records are provided.

This is enforced at two layers: the system prompt injection and the parameterized SQL queries in the tool executor.

### 1.3 23 Typed MCP Tool Definitions
We defined **23 strict JSON Schema tool definitions** (Model Context Protocol) covering:
- Attendance queries (filtered by section, department, threshold)
- Fee defaulter detection with balance calculations
- CGPA and marks reports across multiple exam types
- Scholarship and category-wise student analytics
- Extracurricular and eligibility tracking
- PDF/Excel report generation with professional A4 styling
- WhatsApp notification dispatch

### 1.4 Smart Fallback Pipeline (Zero-Latency Simple Queries)
For strictly procedural queries ("How many students are there?"), a rule-based keyword router immediately hits the DB bypassing the LLM — saving 2–5 seconds of inference time for trivial lookups.

---

## 2. Impact Potential (30%)

Education infrastructure in Tier-2 and Tier-3 institutions globally relies on clunky, undocumented legacy systems. Student data sits siloed, leading to delayed interventions.

### Measurable Impact
- **Administrative Hours Saved**: Natural language → report generation reduces a 3-hour manual export to ~3 seconds. We estimate **10+ hours saved per administrative block per week**.
- **Proactive Student Intervention**: "Show students below 75% attendance" — one query, instant results. Institutions can now act before the semester ends.
- **Parent Outreach Automation**: AIRA triggers the WhatsApp microservice (`whatsapp-web.js`) to send localized, personalized parent alerts directly from a chat prompt.
- **Scholarship Detection**: Category-wise and caste/community reports help institutions identify scholarship-eligible students who may be missed in manual review.

---

## 3. Technical Execution (25%)

### Stack
- **Frontend**: Vanilla HTML5, CSS3, ES6 JavaScript — zero-dependency, instant load on low-end hardware.
- **Backend**: Python 3.10+ Flask, PyMySQL, ReportLab, WeasyPrint, OpenPyXL.
- **Database**: MySQL via XAMPP (offline-ready, no cloud dependency).
- **AI Engine**: Google Gemma 4 (`gemma4:e4b`) via Ollama REST API.
- **Alerting**: Node.js + `whatsapp-web.js` microservice.

### Security Design
- Gemma 4 does **not write raw SQL**. It outputs structured JSON tool calls against our 23-schema MCP tool definitions, which are executed via fully parameterized PyMySQL queries — eliminating SQL injection risk.
- JWT authentication with 24-hour token expiry on all API endpoints.
- Role-based DB context window ensures data isolation at the LLM reasoning level.

### Hardware Optimization
- `num_ctx` capped at 4096 tokens — prevents OOM on 8GB RAM machines.
- Sliding conversation window (last 5 messages) — prevents context overflow.
- Smart Fallback router — bypasses the LLM entirely for simple integer queries.

---

## 4. Accessibility & Offline-First (15%)

### 100% Offline Capable
The entire system (Database → Flask API → Gemma 4 reasoning → PDF Generation → WhatsApp dispatch) runs completely disconnected from the internet:
- `gemma4:e4b` runs via Ollama on the local machine. No cloud API keys required.
- MySQL database is local (XAMPP). No external DB service.
- Frontend is served from a local Python HTTP server. No CDN.

### One-Command Setup
```bash
uv run python setup_project.py   # Creates DB, injects schema, seeds 1500+ records
uv run python start_server.py    # Boots all three services + prints QR code for LAN access
```

### LAN Access with QR Code
The `start_server.py` orchestrator detects the machine's LAN IP and prints a terminal QR code — enabling any device on the same Wi-Fi (e.g., a teacher's phone) to access the system immediately via `http://<LAN-IP>:9000/login.html`.

### Graceful UI Status Indicators
The frontend continuously polls `localhost:11434` and renders an offline/online AI status badge — so users always know whether AIRA is available.

---

## Verification Guide for Judges

```bash
# 1. Start Ollama with Gemma 4
ollama run gemma4:e4b

# 2. Start XAMPP MySQL (port 3306)

# 3. Auto-initialize the system
uv run python setup_project.py

# 4. Boot all services
cd backend && uv run python ../start_server.py

# 5. Open: http://localhost:9000/login.html
#    Login: superadmin / Admin@123

# Try these AIRA prompts:
# "Show me students with less than 75% attendance"
# "Who are the top 10 students by CGPA?"
# "How many fee defaulters do we have? Generate a beautiful PDF report."
# "Send a WhatsApp alert to all fee defaulters"
```
