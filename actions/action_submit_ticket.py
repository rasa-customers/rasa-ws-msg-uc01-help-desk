# Submit IT support ticket (e.g. ServiceNow) and set ticket_number / ticket_priority slots

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict


class ActionSubmitTicket(Action):
    """Submit a support ticket and set ticket_number and ticket_priority slots."""

    def name(self) -> Text:
        return "action_submit_ticket"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        # Infer urgency from conversation (e.g. "board meeting in 2 hours" -> p1_critical)
        last_user = (tracker.latest_message.get("text") or "").lower()
        time_sensitive = any(
            phrase in last_user
            for phrase in [
                "meeting",
                "urgent",
                "asap",
                "hours",
                "deadline",
                "critical",
            ]
        )
        priority = "p1_critical" if time_sensitive else "standard"

        # TODO: call ServiceNow (or other) API to create ticket; use returned case number
        ticket_number = "INC123456"

        return [
            SlotSet("ticket_number", ticket_number),
            SlotSet("ticket_priority", priority),
        ]
