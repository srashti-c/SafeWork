# SafeWork - Project Context (paste this at the start of every new chat)

## What it is
B.Tech CSE final-year project (Medicaps University, Indore). Privacy-preserving workplace
grievance documentation + case-triage platform. Works ALONGSIDE the Internal Committee (IC)
and SHe-Box, never replaces them. NO component decides truth or guilt.

## Stack
- Backend: Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Alembic
- Auth: JWT (python-jose), passlib/bcrypt, RBAC (roles: employee, reviewer, ic_admin)
- NLP: spaCy, scikit-learn, sentence-transformers
- Frontend: React + Vite, Tailwind CSS, Chart.js
- Infra: Docker Compose (db + backend)

## Folder structure
safework/
  docker-compose.yml
  backend/app/{core,api,models,schemas,services}, backend/tests
  ml/        (datasets, training notebooks/scripts, saved models)
  frontend/  (React app, Phase 7)
  docs/

## Key design rules
1. Three privacy modes: identified | confidential | pseudonymous. Never claim absolute anonymity.
2. Identity is stored in a SEPARATE table from case content; complaints reference identity only
   through a restricted, role-gated reference. All identity access is audit-logged.
3. Evidence: SHA-256 hash at upload + timestamp + uploader + case ID. Integrity only, not legal admissibility.
4. Risk score is rule-weighted and explainable (severity, frequency, power imbalance, threat language,
   retaliation flag, recurrence, evidence). Levels: LOW/MEDIUM/HIGH/CRITICAL. Priority only, never probability of guilt.
5. Pattern alerts: semantic similarity above threshold, never auto-names/accuses anyone.
6. Retaliation flag: adverse employment event within N days after complaint -> prompt for human review only.
7. NLP: baseline TF-IDF + LogReg/SVM vs sentence-transformer + classifier. Evaluate with accuracy,
   precision, recall, F1, confusion matrix on held-out set. Data will be synthetic/limited (state as limitation).

## DB entities (planned)
Users, EmployeeReviewerProfiles, Complaints, Categories, Evidence, Witnesses, CaseAssignments,
CaseStatusHistory, RiskAssessments, AIPredictions, PatternAlerts, AuditLogs

## Build phases
0 Setup  1 Auth+RBAC+audit  2 Schema+privacy modes+complaints  3 Evidence hashing
4 NLP (dataset, baseline, transformer, metrics)  5 Risk score  6 Pattern+retaliation
7 React dashboards  8 Testing + report

## Current status
- [x] Phase 0: skeleton, docker-compose, /health and /health/db endpoints, tests
- [ ] Phase 1: auth, RBAC, audit logging   <-- NEXT

## Decisions log
(add one line per decision as you go)
