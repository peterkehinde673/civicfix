# CivicFix Architecture

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
