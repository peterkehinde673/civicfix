import os

os.makedirs('docs/architecture', exist_ok=True)
os.makedirs('docs/screenshots', exist_ok=True)

open('docs/JUDGE_GUIDE.md', 'w', encoding='utf-8').write('''# CivicFix — Judge Quick Start Guide (2 Minutes)

Welcome Hackathon Judges! This guide allows you to evaluate **CivicFix** in under 2 minutes.

---

## ⚡ 30-Second Test Drive
1. **Open Live App**: [https://civicfix-c13b.onrender.com/](https://civicfix-c13b.onrender.com/)
2. **Select Scenario**: Choose from the dropdown (e.g., Scenario 1: Streetlight or Scenario 2: Drainage).
3. **Click Demo**: Click **"⚡ Run Autonomous Demo"**.
4. **Inspect Case**: Click on the generated case in the table (`CF-2026-0001`).

---

## 🔍 Key Agent Features
- **Gemini Multimodal Reasoning**: Structured JSON extraction, priority, and required proof checklist.
- **Blind Trust Rejection**: Department claims 'Fixed', agent rejects it because zero proof was provided.
- **Multimodal Verification**: Field crew uploads photo, Gemini verifies illuminated fixture.
- **Immutable Audit Trail**: Nanosecond-stamped tool execution ledger.
''')

open('docs/DEMO_SCRIPT.md', 'w', encoding='utf-8').write('''# CivicFix — 4-Minute Video Demo Script

**Live URL**: https://civicfix-c13b.onrender.com/  
**Repository**: https://github.com/peterkehinde673/civicfix  

- **0:00 - 0:30 (Problem)**: Community issues get lost or prematurely closed when contractors claim 'Fixed' without proof.
- **0:30 - 1:00 (Solution)**: CivicFix is an autonomous resolution agent built with Google Gemini 3.6 Flash and Google ADK.
- **1:00 - 1:45 (Perception)**: Multimodal ingestion categorizes issues, assesses safety priority, and sets required evidence.
- **1:45 - 2:30 (Killer Feature)**: Department claims completion; CivicFix rejects blind trust, demands photographic proof, and moves status to AWAITING_EVIDENCE.
- **2:30 - 3:15 (Verification)**: Field crew uploads repair photo; Gemini verifies photo against defect (94% confidence).
- **3:15 - 4:00 (Closure & Audit)**: Case resolves autonomously; immutable audit ledger stored in Firestore.
''')

open('docs/screenshots/README.md', 'w', encoding='utf-8').write('''# CivicFix — Screenshot Gallery

| File Name | Description | Judging Criterion |
|:---|:---|:---|
| `dashboard.png` | Operations dashboard with 6 metric cards and stream table | UI & Operations |
| `report.png` | Incident intake form with location and image upload | Multimodal Intake |
| `analysis.png` | Inspector modal showing Gemini structured reasoning | Gemini Innovation |
| `verification.png` | Visual evidence proof card submitted by field crew | Verification Feature |
| `audit-trail.png` | Immutable audit trail showing blind-trust rejection | Security & Audit |
''')

open('docs/architecture/civicfix-architecture.md', 'w', encoding='utf-8').write('''# CivicFix Architecture

```mermaid
flowchart TD
    U[Citizen] --> UI[CivicFix Web Dashboard]
    UI --> API[FastAPI Async Server]
    API --> AGENT[Google ADK CivicFix Agent]
    AGENT --> GEMINI[Google Gemini 3.6 Flash]
    AGENT --> TOOLS[Deterministic Tools]
    TOOLS --> FS[(Google Cloud Firestore)]
    AGENT --> PS[Google Cloud Pub/Sub]
    PS --> WORKER[Async Workflow Worker]
''')
open('README.md', 'w', encoding='utf-8').write('''# CivicFix — Autonomous Community Resolution Engine
![alt text](https://img.shields.io/badge/Live_Demo-civicfix--c13b.onrender.com-blue?style=for-the-badge)

![alt text](https://img.shields.io/badge/GitHub-peterkehinde673%2Fcivicfix-black?style=for-the-badge)

![alt text](https://img.shields.io/badge/Google_Gemini-3.6_Flash-8E75B2?style=for-the-badge)

![alt text](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge)
Autonomous municipal incident lifecycle orchestrator that converts unstructured citizen reports into verified physical resolutions without blind trust.
🚀 Live Demo
https://civicfix-c13b.onrender.com/
🔄 Core Agent Loop
REPORT → UNDERSTAND → PLAN → ACT → WAIT → VERIFY → ESCALATE → RESOLVE
🏗️ Architecture
flowchart TD
    U[Citizen] --> UI[CivicFix Web Dashboard]
    UI --> API[FastAPI Async Server]
    API --> AGENT[Google ADK CivicFix Agent]
    AGENT --> GEMINI[Google Gemini 3.6 Flash]
    AGENT --> TOOLS[Deterministic Tools]
    TOOLS --> CASE[Case Tool]
    TOOLS --> ROUTE[Routing Tool]
    TOOLS --> WO[Work Order Tool]
    TOOLS --> VERIFY[Verification Tool]
    CASE --> FS[(Google Cloud Firestore)]
    AGENT --> PS[Google Cloud Pub/Sub]
    PS --> WORKER[Async Workflow Worker]
🔍 The Key Innovation: Rejecting Blind Trust
When a department claims an issue is fixed without evidence:
Agent intercepts premature claim.
Changes status to AWAITING_EVIDENCE.
Demands post-repair photographic proof.
Gemini verifies visual evidence (confidence >= 0.90).
Case closes only after verified resolution.
🎯 5 Autonomous Demo Scenarios
Streetlight Failure -> High Priority Street Lighting dispatch.
Drainage & Flooding -> Critical Priority Drainage dispatch.
Road Pothole -> High Priority Roads dispatch.
Waste Accumulation -> Waste Management dispatch.
Water Pipe Burst -> Water Department dispatch.
☁️ Google Technologies
Google Gemini 3.6 Flash: Multimodal perception & resolution verification.
Google ADK Pattern: Structured tool execution & lifecycle loop.
Google Cloud Firestore: Dual-mode state persistence & audit logging.
Google Cloud Pub/Sub: Asynchronous workflow event messaging.
Google Cloud Run: Container deployment ready
🛠️ Quick Start
git clone https://github.com/peterkehinde673/civicfix.git
cd civicfix
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
🧪 Run Tests
pytest -v
''')
print('SUCCESS: All files generated successfully!')
