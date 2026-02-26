# Submit IT support ticket to ServiceNow and set ticket_number / ticket_priority slots

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Text

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict

logger = logging.getLogger(__name__)

SN_INSTANCE_URL = os.getenv("SN_INSTANCE_URL")  # e.g. https://devXXXXX.service-now.com
SN_USERNAME = os.getenv("SN_USERNAME")
SN_PASSWORD = os.getenv("SN_PASSWORD")

# ServiceNow urgency/impact mapping — lower number = higher severity
PRIORITY_MAP = {
    "p1_critical": {"urgency": "1", "impact": "1"},
    "standard":    {"urgency": "3", "impact": "3"},
}

ISSUE_LABELS = {
    "vpn": "VPN",
    "company_portal": "Company Portal",
    "other_work_tool": "Internal Work Tool",
}


def _build_description(tracker: Tracker) -> str:
    """Compose a rich incident description from conversation slots."""
    issue_type = tracker.get_slot("connection_issue_type") or "unknown"
    error_msg = tracker.get_slot("error_message_text")
    last_connected = tracker.get_slot("last_successful_connection")
    network = tracker.get_slot("current_network")

    parts = [f"Connectivity issue with: {ISSUE_LABELS.get(issue_type, issue_type)}"]
    if error_msg:
        parts.append(f"Error message: {error_msg}")
    if last_connected:
        parts.append(f"Last successful connection: {last_connected}")
    if network:
        net_label = "Home Wi-Fi" if network == "home_wifi" else network
        parts.append(f"Current network: {net_label}")

    return "\n".join(parts)


async def create_incident_snow(
    short_description: str,
    description: str,
    urgency: str,
    impact: str,
) -> str:
    """Creates an Incident in ServiceNow via the Table API and returns the INC number."""
    url = f"{SN_INSTANCE_URL}/api/now/table/incident"

    payload = {
        "short_description": short_description,
        "description": description,
        "urgency": urgency,
        "impact": impact,
        "category": "Network",
    }

    logger.warning(
        "SNOW request -> POST %s | user=%s | payload=%s",
        url, SN_USERNAME, payload,
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            auth=(SN_USERNAME, SN_PASSWORD),
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=15,
        )

    body = response.text
    logger.warning(
        "SNOW response <- status=%s | content-type=%s | body=%s",
        response.status_code,
        response.headers.get("content-type", "N/A"),
        body[:1000] if body else "(empty)",
    )

    if response.status_code >= 400:
        raise Exception(
            f"ServiceNow returned HTTP {response.status_code}: {body[:500]}"
        )

    if not body.strip():
        raise Exception(
            f"ServiceNow returned an empty response (HTTP {response.status_code}). "
            "Check that SN_USERNAME / SN_PASSWORD are correct and the user has the "
            "rest_api_explorer or snc_platform_rest_api_access role."
        )

    try:
        data = response.json()
    except Exception:
        raise Exception(
            f"ServiceNow returned non-JSON (HTTP {response.status_code}): {body[:500]}"
        )

    result = data.get("result", {})
    incident_number = result.get("number")
    if incident_number:
        return incident_number
    raise Exception(
        f"Failed to retrieve incident number from ServiceNow response. Details: {result}"
    )


class ActionSubmitTicket(Action):
    """Submit a support ticket to ServiceNow and set ticket_number / ticket_priority slots."""

    def name(self) -> Text:
        return "action_submit_ticket"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        last_user = (tracker.latest_message.get("text") or "").lower()
        time_sensitive = any(
            phrase in last_user
            for phrase in ["meeting", "urgent", "asap", "hours", "deadline", "critical"]
        )
        priority = "p1_critical" if time_sensitive else "standard"
        sn_fields = PRIORITY_MAP[priority]

        issue_type = tracker.get_slot("connection_issue_type") or "unknown"
        short_desc = f"Connectivity issue – {ISSUE_LABELS.get(issue_type, issue_type)}"
        description = _build_description(tracker)

        try:
            ticket_number = await create_incident_snow(
                short_description=short_desc,
                description=description,
                urgency=sn_fields["urgency"],
                impact=sn_fields["impact"],
            )
        except Exception:
            logger.exception("ServiceNow incident creation failed")
            dispatcher.utter_message(
                text="I'm sorry, I wasn't able to create the ticket right now. "
                     "Please try again in a moment or contact IT support directly."
            )
            return []

        priority_label = "P1 – Critical" if priority == "p1_critical" else "Standard"
        issue_label = ISSUE_LABELS.get(issue_type, issue_type)
        error_msg = tracker.get_slot("error_message_text")
        network = tracker.get_slot("current_network")
        net_label = "Home Wi-Fi" if network == "home_wifi" else (network or "N/A")

        summary_lines = [
            f"Ticket: {ticket_number}",
            f"Priority: {priority_label}",
            f"Category: Network / {issue_label}",
        ]
        if error_msg:
            summary_lines.append(f"Error: {error_msg}")
        summary_lines.append(f"Network: {net_label}")

        return [
            SlotSet("ticket_number", ticket_number),
            SlotSet("ticket_priority", priority),
            SlotSet("ticket_summary", "\n".join(summary_lines)),
        ]
