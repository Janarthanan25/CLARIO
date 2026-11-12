<<<<<<< HEAD
# CLARIO – Unified AI Workspace, Intelligent Communication & Payment Security Platform

[![Python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.0-000000.svg?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-22%20Passed-10B981.svg)](tests/)
[![Security](https://img.shields.io/badge/Security-CSRF%20%7C%20PBKDF2%20%7C%20RBAC-2563EB.svg)]()
[![Gemini API](https://img.shields.io/badge/AI%20Engine-Google%20Gemini-4285F4.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)

CLARIO is an enterprise-grade AI operating platform that unifies **document intelligence**, **smart email automation**, and **machine-learning payment security** into a single cohesive SaaS workspace.

Built with **Flask**, **SQLite / SQLAlchemy**, **Bootstrap 5**, **Chart.js**, **Lucide Icons**, **Google Gemini API**, **Scikit-Learn**, and **PayPal Sandbox REST v2**.

---

## 🌟 Key Platform Modules

### 1. Module A: CLARIO AI Workspace (Document Intelligence)
- **Multi-Format Ingestion**: Drag-and-drop parsing for PDF (`PyMuPDF / fitz`), DOCX (`python-docx`), TXT, and CSV (`pandas`).
- **Context-Grounded Q&A**: Document-grounded contextual answering citing verified facts present in uploaded files.
- **Safe Markdown Rendering**: Displays executive summaries, entity cards, and Q&A chat messages with sanitized GitHub-Flavored Markdown, tables, lists, and syntax-highlighted code blocks via `marked.js`, `DOMPurify`, and `highlight.js`.
- **Temporal Marker Extraction**: Extracts critical financial commitments, filing deadlines, and milestones automatically.
- **CSV Data Analytics**: Schema discovery, statistical profiling (min, max, mean, missing values), and dynamic Chart.js chart generation (bar, line, and distribution charts).
- **Export & Management**: Download compiled Markdown intelligence reports or delete files securely.

### 2. Module B: CLARIO Smart Email Assistant
- **Inbound Analysis**: Evaluates raw email text for sentiment (Positive, Neutral, Negative) and urgency ratings (0.0 to 1.0).
- **Categorization**: Auto-sorts correspondence into *Important*, *Work*, *Personal*, *Finance*, *Promotions*, or *Urgent*.
- **Task & Deadline Extraction**: Discovers action items, follow-ups, and calendar deadlines using NLP heuristics.
- **Multi-Tone Reply Drafting**: Composes ready-to-dispatch responses in *Professional*, *Friendly*, or *Formal* tones.
- **Safe Workflow Guarantee**: Clario only drafts responses; no external emails are dispatched without explicit human authorization.

### 3. Module C: CLARIO Security AI (Payment Defense)
- **Transaction Surveillance**: Ingests transactions via CSV upload or pre-loaded demonstration datasets.
- **Hybrid Anomaly Detection**:
  - *Deterministic Rule Engine*: Catches duplicate charges to identical recipients within 60 minutes and velocity spikes (4+ transactions in 15 minutes).
  - *Scikit-Learn Machine Learning*: Uses unsupervised `IsolationForest` on feature vectors `[amount, log(amount), hour_of_day]` to detect multidimensional statistical outliers.
- **Indicative Risk Scoring**: Evaluates transactions with confidence scores (0.0 – 100.0) mapped to **LOW**, **MEDIUM**, and **HIGH** risk levels.
- **Explainable Diagnostics**: Explains exactly which indicators triggered the rating and recommends concrete remediation steps.
- **Manual Review Controls**: Compliance analysts can manually approve transactions or flag them as fraud with instant status updates.

### 4. Advanced Multi-Agent Orchestration System
CLARIO coordinates 6 autonomous agents executing real backend tasks:
1. **Master Orchestrator Agent**: Decomposes natural language queries from the Global Command Center, evaluates requirements, selects specialist tools, and synthesizes final briefings.
2. **Document Agent**: Handles document parsing, summarization, entity extraction, and grounded Q&A.
3. **Email Agent**: Analyzes email context and drafts multi-tone responses.
4. **Security Agent**: Evaluates transactions and detects payment anomalies.
5. **Research Agent**: Cross-references files, emails, and transaction notes for unified synthesis.
6. **Report Agent**: Compiles cross-module telemetry into downloadable executive reports.

### 5. PayPal Sandbox Payment & Subscriptions
- **Subscription Tiers**:
  - **FREE Starter**: 5 Document uploads, 25 AI queries/day, community support.
  - **PRO Suite ($29.00/mo)**: Unlimited documents, 500 AI queries/day, multi-agent orchestration, Isolation Forest fraud security.
- **Server-Side REST Verification**: Utilizes PayPal Orders v2 REST API for order creation (`/api/paypal/create-order`) and capture verification (`/api/paypal/capture-order`).
- **Zero Card Storage**: Zero credit card numbers or raw billing secrets stored. Instant server-side activation on verified capture.
- **Simulated Sandbox Test**: Includes a built-in sandbox test engine for verification without requiring external sandbox account logins.

---

## 🎨 Design System

CLARIO implements a modern light-themed SaaS visual direction:
- **Main Background**: `#F8FAFC`
- **Sidebar**: `#FFFFFF`
- **Primary Blue**: `#2563EB`
- **Secondary Violet**: `#7C3AED`
- **Accent Cyan**: `#06B6D4`
- **Main Text**: `#172033`
- **Secondary Text**: `#64748B`
- **Borders**: `#E2E8F0`
- **Typography**: Plus Jakarta Sans & JetBrains Mono

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- **Python**: Version 3.10 to 3.13
- **Git**

### 2. Clone Repository & Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/your-username/CLARIO.git
cd CLARIO

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# On Windows:
copy .env.example .env
# On macOS/Linux:
cp .env.example .env
```

Open `.env` and fill in your configuration:
```ini
# Flask Core
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secure-random-32-byte-hex-string

# Google Gemini API (Optional - runs in deterministic fallback mode if empty)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# PayPal Sandbox (Optional - simulated sandbox active if empty)
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Default Demonstration Credentials

The platform automatically seeds a pre-configured administrator account on initial startup:
- **Email**: `admin@clario.ai`
- **Password**: `Admin123!`
- **Role**: `admin`
- **Plan**: `PRO`

You can also register a new account on the `/register` page at any time.

---

## 🧪 Automated Testing

CLARIO features a complete test suite covering authentication, document processing, email classification, anomaly detection, agent routing, payments, and Markdown rendering.

To run the automated test suite:
```bash
pytest -v
```

Expected result:
```
====================== 22 passed in ~12s ======================
```

To run the pre-upload security secret scanner:
```bash
python tests/secret_scanner.py
```

---

## 📁 Project Architecture

```
CLARIO/
├── app.py                      # Application factory, extensions & error handlers
├── config.py                   # Configuration, tiers & environment resolution
├── extensions.py               # Flask-WTF CSRFProtect extension instance
├── requirements.txt            # Production & development dependencies
├── DEVELOPMENT_STATUS.md       # Development milestone tracker
├── .env.example                # Sanitized environment template (safe for Git)
├── .gitignore                  # Production Git ignore rules
│
├── agents/                     # Multi-Agent Orchestration
│   ├── master_agent.py         # Master Orchestrator (dispatch & synthesis)
│   ├── document_agent.py       # Document Intelligence Specialist
│   ├── email_agent.py          # Email Assistant Specialist
│   ├── security_agent.py       # Payment Defense Specialist
│   ├── research_agent.py       # Cross-Module Correlation Specialist
│   └── report_agent.py         # Executive Briefing Specialist
│
├── modules/                    # Business Logic Engines
│   ├── workspace/              # Document extraction & CSV stats (PyMuPDF, docx, pandas)
│   ├── email/                  # Email NLP analysis, task extraction & tone drafting
│   └── security/               # Rule engine + Scikit-Learn IsolationForest
│
├── payments/                   # Payment Gateway
│   ├── paypal.py               # PayPal REST v2 client & capture verification
│   └── webhooks.py             # Webhook event processing
│
├── models/                     # Database Models (12 SQLAlchemy Models)
│   ├── __init__.py             # SQLAlchemy db instance
│   └── models.py               # User, Document, Conversation, Message, EmailRecord,
│                               # Transaction, RiskResult, AgentExecution, Payment, etc.
│
├── routes/                     # Blueprint Endpoints
│   ├── auth_routes.py          # Register, login, logout, password validation
│   ├── dashboard_routes.py     # Overview metrics & Global Command Center
│   ├── workspace_routes.py     # File upload, grounded Q&A, CSV analytics
│   ├── email_routes.py         # Email analysis, tone regeneration, approval
│   ├── security_routes.py      # Transaction audits, anomaly scanning, reviews
│   ├── agent_routes.py         # Multi-agent console dispatch & telemetry
│   ├── payment_routes.py       # PayPal orders & subscription upgrades
│   ├── notification_routes.py  # Notification bell & unread counts
│   ├── settings_routes.py      # Profile updates & Gemini API key config
│   ├── admin_routes.py         # User management, telemetry & health checks
│   └── report_routes.py        # Executive briefing generation & downloads
│
├── services/                   # Core Infrastructure Services
│   ├── ai_service.py           # Gemini 3.5 API client with automatic model failover
│   ├── notification_service.py # In-app notification dispatcher
│   └── audit_service.py        # Immutable security audit trail logger
│
├── utils/                      # Utilities & Demo Data
│   ├── sample_data.py          # Demo transactions, emails, and financial reports
│   └── security_utils.py       # Role decorators & file sanitization
│
├── templates/                  # Jinja2 HTML5 Templates
│   ├── base.html               # Master layout, navigation, and script bundles
│   ├── index.html              # 10-section SaaS Landing Page
│   ├── login.html              # Secure Login with demo credential fill
│   ├── register.html           # Registration with password validation
│   ├── dashboard.html          # Global Command Center & Chart.js
│   ├── workspace.html          # Document Intelligence & Grounded Q&A
│   ├── email.html              # Email Assistant with tone switcher
│   ├── security.html           # Transaction security surveillance table
│   ├── agents.html             # Multi-Agent Matrix & live execution console
│   ├── payments.html           # Pricing table & PayPal checkout
│   ├── reports.html            # Executive Briefings & Markdown downloads
│   ├── settings.html           # API Keys & profile configuration
│   └── admin.html              # Admin Governance Dashboard
│
├── static/                     # Static Web Assets
│   ├── css/custom.css          # Design system styling & markdown styles
│   └── js/                     # Modular frontend controllers
│       ├── main.js             # Global CSRF fetch wrapper & safe markdown renderer
│       ├── dashboard.js        # Command center & Chart.js instances
│       ├── workspace.js        # Document dropzone & grounded chat
│       ├── email.js            # Email assistant & tone switchers
│       ├── security.js         # Transaction review modal
│       └── agents.js           # Multi-agent matrix console
│
└── tests/                      # Automated Test Suite (22 Tests)
    ├── conftest.py             # Test fixtures & memory database setup
    ├── secret_scanner.py       # Pre-commit secret leak scanner
    ├── test_auth.py            # Authentication & RBAC tests
    ├── test_workspace.py       # Document processing & chat tests
    ├── test_email.py           # Email analysis & tone tests
    ├── test_security.py        # Anomaly detection & review tests
    ├── test_agents.py          # Multi-agent routing tests
    ├── test_payments.py        # PayPal order creation & capture tests
    ├── verify_gemini_live.py   # Live Gemini API verification script
    └── verify_markdown_rendering.py # Markdown parser & grounded wording checks
```

---

## 🔒 Security & Privacy Safeguards

- **Zero Secret Exposure**: `.env` is strictly excluded from version control via `.gitignore`. An example template `.env.example` provides sanitized placeholders only.
- **CSRF Protection**: All state-changing endpoints are protected by `Flask-WTF` CSRF tokens with automatic client header injection.
- **Password Security**: Passwords are cryptographically salted and hashed using `werkzeug.security` (PBKDF2 with SHA-256). Plaintext passwords are never stored.
- **Role-Based Access Control**: Administrative actions and dashboards are restricted by `@admin_required` decorators and enforced at the database level.
- **Safe Document Ingestion**: Uploads are restricted to approved formats (`.pdf`, `.docx`, `.txt`, `.csv`), sanitized using `secure_filename`, capped at 16MB, and isolated in `uploads/` (excluded from Git).
- **Client-Side HTML Sanitization**: All AI-generated markdown is parsed with `marked.js` and sanitized through `DOMPurify` before DOM insertion to prevent Cross-Site Scripting (XSS).
- **Zero Card Storage**: Payment processing utilizes PayPal Orders REST v2 server-to-server capture verification. No credit card numbers or raw billing data touch CLARIO servers.
- **Audit Trails**: Security audits, user logins, role changes, and file uploads are immutably logged to the database.

---

## 📄 License
MIT License. Built for the CLARIO Unified AI Platform.
=======
# CLARIO
>>>>>>> a9822772c4f62eed6e295fab94284a8443cd2bfc
