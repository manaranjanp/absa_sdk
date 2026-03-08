"""Escalation Ticket File Tools"""

import json
import os
from datetime import datetime

TICKETS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "escalation_tickets.json")


def create_escalation_ticket(
    review_id: str,
    priority: str,
    sla_hours: int,
    review_summary: str,
) -> str:
    """Create an escalation ticket by appending to the tickets file.

    Args:
        review_id: The review that triggered escalation.
        priority: Ticket priority (HIGH/MEDIUM/LOW).
        sla_hours: SLA in hours for resolution.
        review_summary: Brief summary of the review for ticket context.

    Returns:
        JSON string with ticket details.
    """
    os.makedirs(os.path.dirname(TICKETS_FILE), exist_ok=True)

    ticket = {
        "review_id": review_id,
        "priority": priority,
        "sla_hours": sla_hours,
        "review_summary": review_summary,
        "created_at": datetime.utcnow().isoformat(),
    }

    with open(TICKETS_FILE, "a") as f:
        f.write(json.dumps(ticket) + "\n")

    return json.dumps({
        "action": "CREATED",
        "priority": priority,
        "sla_hours": sla_hours,
    })
