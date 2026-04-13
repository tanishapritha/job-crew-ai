---
title: Job Crew
emoji: 🚀
colorFrom: gray
colorTo: indigo
sdk: docker
pinned: false
---

# Job Automation System Backend

A production-ready Job Automation SaaS backend built with **FastAPI** for pure, deterministic CRUD business logic, and **CrewAI** strictly allocated to the heuristic and generative job pipeline. 

Data is securely managed using **Google Sheets** (`gspread`), enabling seamless real-time visibility for non-technical stakeholders without the overhead of heavy RDBMS setups.

## Features
- **FastAPI Layer**: Handling of User state, Authentication, Session logic, Approvals, Admin analytics. 
- **CrewAI Layer**: Orchestration of autonomous agents explicitly for scraping ADZUNA API, semantic filtering, rendering HTML digests, and dispensing them via SMTP.
- **Database**: Single-source-of-truth via modular interaction mapped to Google Spreadsheet tabs.
- **Scheduler**: Out of the box integration with APScheduler via lifespan events inside ASGI spec.

## Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Define env file using `.env.example`.
3. Obtain Google service account JSON and map to `.env`.
4. Run locally via: `uvicorn main:app --reload`
