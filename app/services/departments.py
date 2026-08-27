import uuid
from typing import Dict, Any, List

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


class DepartmentSimulator:
    """
    Simulated Municipal Department Service (Demo Simulation).
    Simulates municipal responses, work order lifecycle, and resolution claims.
    """

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
        """Simulates department claiming 'Job Done' without providing photographic proof."""
        return {
            "department": department,
            "status": "COMPLETED",
            "claim_text": f"[Demo Simulation] Field crew reports that the issue ({issue_summary}) has been addressed and marked completed in internal ticketing system.",
            "has_evidence": False,
            "requires_verification": True
        }

    @staticmethod
    def simulate_resolution_evidence(category: str) -> Dict[str, Any]:
        """Simulates field unit submitting after-repair photographic proof."""
        return {
            "evidence_id": f"EVD-{uuid.uuid4().hex[:6].upper()}",
            "description": f"[Demo Simulation] Verified post-repair photographic proof submitted by field team for {category}.",
            "timestamp": "2026-08-27T20:45:00Z",
            "verified_by_supervisor": True,
            "simulated_image": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='200' style='background:%23064E3B;color:%23fff;font-family:sans-serif;'><text x='20' y='100' font-size='18' fill='%236EE7B7'>Field Resolution Proof: Repaired & Operational</text></svg>"
        }


department_simulator = DepartmentSimulator()
