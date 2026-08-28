# CivicFix — Autonomous Community Resolution Engine

[![Live Demo](https://img.shields.io/badge/Live_Demo-civicfix--c13b.onrender.com-blue?style=for-the-badge)](https://civicfix-c13b.onrender.com/)
[![GitHub](https://img.shields.io/badge/GitHub-peterkehinde673%2Fcivicfix-black?style=for-the-badge)](https://github.com/peterkehinde673/civicfix)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.6_Flash-8E75B2?style=for-the-badge)](https://ai.google.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge)](https://fastapi.tiangolo.com/)

> **Autonomous municipal incident lifecycle orchestrator that converts unstructured citizen reports into verified physical resolutions without blind trust.**

---

## 🚀 Live Demo

**Public Application URL**: [https://civicfix-c13b.onrender.com/](https://civicfix-c13b.onrender.com/)

---

## 🏛️ Problem

Municipal complaint systems across the world suffer from three key failures:
1. **Unstructured Data Bottleneck**: Citizen reports arrive via fragmented channels with vague descriptions and unverified photos, creating routing delays.
2. **Premature Ticket Closure (The "Ghost Repair")**: Field contractors and departments mark tickets as "Resolved" without verifiable physical proof.
3. **Zero Continuous Auditing**: Citizens lack visibility into why a case was routed, what priority was assigned, and how claimed resolutions were verified.

---

## 💡 Solution

**CivicFix** replaces passive ticketing forms with an **autonomous operations agent**. Rather than just storing a complaint, CivicFix:
- **Perceives & Reasons**: Extracts structured metadata (defect type, severity, priority, precise location) using **Google Gemini 3.6 Flash**.
- **Dispatches Work Orders**: Selects the appropriate municipal department and dispatches work orders via deterministic tools.
- **Rejects Blind Trust**: Intercepts premature closure claims, moves tickets to `AWAITING_EVIDENCE`, and demands photographic proof.
- **Multimodally Verifies**: Evaluates post-repair photos against the original defect before permitting ticket closure.
- **Audits Every Step**: Generates an immutable, timestamped audit log.

---

## 🔄 Core Agent Loop
---

## 🏗️ Architecture

```mermaid
flowchart TD
    U[Citizen / User] --> UI[CivicFix Web Dashboard]
    UI --> API[FastAPI Async API Server]
    API --> AGENT[Google ADK CivicFix Agent]
    AGENT --> GEMINI[Google Gemini 3.6 Flash]
    AGENT --> TOOLS[Deterministic Tool Suite]

    TOOLS --> CASE[Case Management Tool]
    TOOLS --> ROUTE[Department Routing Tool]
    TOOLS --> WO[Work Order Dispatch Tool]
    TOOLS --> EVD[Evidence Analysis Tool]
    TOOLS --> VERIFY[Resolution Verification Tool]
    TOOLS --> ESCALATE[Escalation Tool]

    CASE --> FS[(Google Cloud Firestore)]
    VERIFY --> GEMINI
    AGENT --> PS[Google Cloud Pub/Sub]
    PS --> WORKER[Async Workflow Worker]
    WORKER --> DEPT[Simulated Municipal Ecosystem]
    DEPT --> PS
    FS --> AGENT
flowchart TD
    A[Citizen Submits Report\nText + Visual Media] --> B[UNDERSTAND\nGemini Multimodal Reasoning]
    B --> C[PLAN & ACT\nCreate Case & Assign Department]
    C --> D[DISPATCH\nIssue Municipal Work Order]
    D --> E[WAIT / MONITOR\nDepartment Resolution Claim]
    E --> F{EVIDENCE CHECK\nIs Photographic Proof Attached?}
    F -- No Proof / Premature Claim --> G[REJECT BLIND TRUST\nStatus: AWAITING_EVIDENCE]
    G --> H[REQUEST EVIDENCE\nNotify Field Contractor]
    H --> I[Field Submits Post-Repair Proof]
    I --> J[MULTIMODAL VERIFICATION\nGemini Defect Comparison]
    F -- Proof Attached --> J
    J --> K{Verification Evaluation}
    K -- Passed --> L[RESOLVE & CLOSE\nImmutable Audit Stamped]
    K -- Failed / Contradictory --> M[REQUEST FURTHER PROOF]
    K -- Stalled / SLA Breach --> N[ESCALATE\nMunicipal Oversight Board]
git clone https://github.com/peterkehinde673/civicfix.git
cd civicfix
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pytest -v
 Security & Safety
Zero Secret Leakage: API keys and GCP service accounts are loaded from environment variables and excluded from Git via .gitignore.
Input Validation: Multimodal uploads are capped at 10MB with strict base64 and MIME verification.
Structured Fallback: If the Gemini API experiences network interruption, the system activates a deterministic heuristic fallback.
🏆 Hackathon Submission
Hackathon: Google All Things Agentic Hackathon
Track: Autonomous AI Agents & Real-World Operations
Core Technology: Google Gemini 3.6 Flash & Google ADK Architecture
Developer: @peterkehinde673
