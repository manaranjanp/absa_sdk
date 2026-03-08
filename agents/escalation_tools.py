"""
Escalation Ticket File Tools
------------------------------
Function tool for the Policy Evaluation & Escalation Agent to create
escalation tickets by appending JSON lines to a file.
"""

import json
import os
from datetime import datetime

# Path to the escalation tickets file (one JSON object per line)
TICKETS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "escalation_tickets.json")


def create_escalation_ticket(
    review_id: str,
    restaurant_id: str,
    customer_id: str,
    customer_tier: str,
    priority: str,
    sla_hours: int,
    primary_negative_aspect: str,
    review_summary: str
) -> str:
    """Create an escalation ticket by appending to the tickets file.

    Args:
        review_id: The review that triggered escalation.
        restaurant_id: The restaurant identifier.
        customer_id: The customer identifier.
        customer_tier: Customer loyalty tier (Platinum/Gold/Silver/Standard).
        priority: Ticket priority (HIGH/MEDIUM/LOW).
        sla_hours: SLA in hours for resolution.
        primary_negative_aspect: The main negative aspect code.
        review_summary: Brief summary of the review for ticket context.

    Returns:
        JSON string with ticket details.
    """
    os.makedirs(os.path.dirname(TICKETS_FILE), exist_ok=True)

    ticket = {
        "review_id": review_id,
        "restaurant_id": restaurant_id,
        "customer_id": customer_id,
        "customer_tier": customer_tier,
        "priority": priority,
        "sla_hours": sla_hours,
        "primary_negative_aspect": primary_negative_aspect,
        "review_summary": review_summary,
        "created_at": datetime.utcnow().isoformat()
    }

    with open(TICKETS_FILE, "a") as f:
        f.write(json.dumps(ticket) + "\n")

    return json.dumps({
        "action": "CREATED",
        "priority": priority,
        "sla_hours": sla_hours,
        "message": f"New {priority} priority ticket created with {sla_hours}h SLA"
    })
