# CivicFix — Autonomous Community Resolution Engine
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
