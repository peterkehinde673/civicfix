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
    A[Citizen Submits Report] --> B[Gemini Multimodal Reasoning]
    B --> C[Plan & Create Case]
    C --> D[Dispatch Work Order]
    D --> E[Monitor Department Response]
    E --> F{Photographic Proof Attached?}
    F -- No Proof / Premature Claim --> G[Reject Blind Trust: Status AWAITING_EVIDENCE]
    G --> H[Request Proof from Contractor]
    H --> I[Field Submits Post-Repair Proof]
    I --> J[Gemini Multimodal Verification]
    F -- Proof Attached --> J
    J --> K{Verification Result}
    K -- Passed --> L[Resolve & Close Case]
    K -- Failed --> M[Request Further Proof]
    K -- Stalled --> N[Escalate to Oversight Board]
