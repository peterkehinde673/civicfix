import uuid
from typing import Dict, Any

AVAILABLE_DEPARTMENTS = [
    "Roads Department",
    "Drainage Department",
    "Street Lighting Department",
    "Waste Management Department",
    "Public Safety Department",
    "Water Department",
    "Public Facilities Department"
]

CATEGORY_TO_DEPARTMENT = {
    "Roads": "Roads Department",
    "Drainage": "Drainage Department",
    "Street Lighting": "Street Lighting Department",
    "Waste Management": "Waste Management Department",
    "Public Safety": "Public Safety Department",
    "Water": "Water Department",
    "Public Facilities": "Public Facilities Department",
    "Other": "Public Facilities Department"
}

# Valid 1x1 green pixel base64 PNG
VALID_PNG_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


class DepartmentSimulator:
    """Simulated Municipal Department Service (Demo Simulation)."""

    @staticmethod
    def get_department_for_category(category: str) -> str:
        return CATEGORY_TO_DEPARTMENT.get(category, "Public Facilities Department")

    @staticmethod
    def simulate_dispatch_acknowledgement(department: str, case_id: str) -> Dict[str, Any]:
        return {
            "department": department,
            "case_id": case_id,
            "status": "ACCEPTED",
            "dispatch_ticket": f"TKT-{uuid.uuid4().hex[:6].upper()}",
            "estimated_response_hours": 24,
            "notes": f"[Demo Simulation] Work order accepted by {department} dispatch unit."
        }

    @staticmethod
    def simulate_premature_resolution(department: str, issue_summary: str) -> Dict[str, Any]:
        return {
            "department": department,
            "status": "COMPLETED",
            "claim_text": f"[Demo Simulation] Field crew reports that the issue ({issue_summary}) has been addressed and marked completed in internal ticketing system.",
            "has_evidence": False,
            "requires_verification": True
        }

    @staticmethod
    def simulate_resolution_evidence(category: str) -> Dict[str, Any]:
        return {
            "evidence_id": f"EVD-{uuid.uuid4().hex[:6].upper()}",
            "description": f"[Demo Simulation] Verified post-repair photographic proof submitted by field team for {category}.",
            "timestamp": "2026-08-28T12:00:00Z",
            "verified_by_supervisor": True,
            "simulated_image": VALID_PNG_BASE64
        }


department_simulator = DepartmentSimulator()
