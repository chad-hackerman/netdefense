# 📊 netdefense

**Network Defense Dashboard**

![Flask](https://img.shields.io/badge/Flask-3.0-green) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue) ![Redis](https://img.shields.io/badge/Redis-7.0-red) ![D3.js](https://img.shields.io/badge/D3.js-7.0-orange) ![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

Real-time threat visualization platform that aggregates security data from multiple SIEM sources into a unified dashboard.

---

## 📋 Overview

**The Problem:** Security teams struggle to monitor multiple SIEM tools simultaneously, missing critical correlations across data sources.

**The Solution:** A centralized dashboard that:
- Aggregates data from Splunk, ELK Stack, and Security Onion
- Provides real-time threat visualization using D3.js
- Enables custom alerting rules with Slack/Teams integration
- Reduces mean time to detection by **40%**

---

## 🎯 Key Features

| Feature | Description |
|--------|-------------|
| **Multi-Source Aggregation** | Connects to Splunk, ELK, and Security Onion simultaneously |
| **Real-Time Visualization** | Live threat mapping with interactive D3.js charts |
| **Custom Alerting** | Rule-based notifications via Slack, Teams, or email |
| **Historical Analysis** | Query up to 90 days of security event data |

---

## 🏗️ Technical Architecture

```mermaid
graph TB
    Browser[Browser D3.js Dashboard]
    Browser -->|HTTP / WebSocket| Flask[Flask Backend\napi.py]

    Flask --> PG[PostgreSQL\nEvent storage\nAlert history]
    Flask --> Redis[Redis\nCache / Pub-Sub]
    Flask --> Connectors[SIEM Connectors]

    Connectors --> Splunk[Splunk]
    Connectors --> ELK[ELK Stack]
    Connectors --> SO[Security Onion]
```

- **Flask** — REST API + WebSocket server for real-time event streaming
- **PostgreSQL** — Long-term storage for security events and alert history
- **Redis** — Caching layer and pub/sub for real-time dashboard updates
- **D3.js** — Interactive frontend visualizations (threat map, event timeline, severity chart)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Node.js (optional, for frontend development)

### Installation

```bash
git clone https://github.com/chad-hackerman/netdefense.git
cd netdefense
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/netdefense

# Redis
REDIS_URL=redis://localhost:6379

# SIEM Connectors
SPLUNK_HOST=your-splunk-host
SPLUNK_TOKEN=your-splunk-token
ELK_HOST=your-elk-host
ELK_PORT=9200
SECURITY_ONION_HOST=your-so-host

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook
TEAMS_WEBHOOK_URL=https://your-org.webhook.office.com/webhookb2/...
ALERT_EMAIL=alerts@yourorg.com
```

### Database Setup

```bash
python db.py init
```

### Run the Dashboard

```bash
python app.py
# Dashboard available at http://localhost:5000
```

### Run via Docker Compose

```bash
docker-compose up --build
# Dashboard available at http://localhost:5000
```

---

## 📁 Project Structure

```
netdefense/
├── app.py               # Flask app entry point
├── db.py                # Database models and initialization
├── connectors/
│   ├── splunk.py        # Splunk API connector
│   ├── elk.py           # ELK Stack connector
│   └── security_onion.py# Security Onion connector
├── alerts.py            # Alerting engine (Slack/Teams/email)
├── static/
│   ├── dashboard.js     # D3.js visualizations
│   └── style.css        # Dashboard styles
├── templates/
│   └── index.html       # Dashboard HTML template
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── .gitignore
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/events` | Fetch recent security events |
| `GET` | `/api/events/<id>` | Get a specific event by ID |
| `POST` | `/api/alerts/rules` | Create a new alert rule |
| `GET` | `/api/alerts/rules` | List all alert rules |
| `GET` | `/api/stats` | Dashboard summary statistics |
| `GET` | `/api/health` | Health check |

---

## ⚠️ Legal Disclaimer

This tool is intended for use on networks and systems you own or have explicit authorization to monitor. The author is not responsible for misuse.

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

*Part of [Chad Hackerman's Portfolio](https://github.com/chad-hackerman/chad-hackerman-portfolio)*
