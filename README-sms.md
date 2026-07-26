<!--
================================================================================
FILE: README.md
VERSION: 1.0.0
REVISION DATE: 2026-07-03
PURPOSE: Project overview, setup instructions, and architecture documentation
DEPENDENCIES: None
USAGE: Read this first when setting up the project
AUTHOR: Ghanshyam Acharya
CODE OWNER: AviaSafeSystems
================================================================================
-->

# Safety-Health - Aviation SMS Maturity Platform

**Safety-Health** is a comprehensive Safety Management System (SMS) maturity assessment platform designed for the Nepalese aviation industry, aligned with ICAO Annex 19 and CAR-19 requirements.

## 🎯 Purpose

- **Airlines**: Assess SMS maturity across 12 elements
- **Safety Officers**: Analyze results and track corrective actions
- **CAAN**: Monitor regulatory compliance across all airlines

## 🏗️ Architecture

| Layer | Technology | Deployment |
|-------|------------|------------|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) | Netlify |
| **Backend** | Python 3.12, FastAPI | Render |
| **Database** | PostgreSQL (Supabase) | Supabase Cloud |

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/safety-health.git
cd safety-health

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup (optional)
cd ../frontend
# No build step - pure HTML/CSS/JS