# Example action API implementation
import httpx

from datetime import datetime, timezone
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.types import DomainDict

class ActionAPI(Action):
    def name(self) -> Text:
        return "action_api"

    async def run(
        self, dispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
      # Get current timestamp & more via API call
      timestamp = get_timestamp()
      # If the timestamp is not found, use the current time
      if timestamp is None:
          timestamp = datetime.now(timezone.utc).isoformat()
      dispatcher.utter_message(text=f"the time is now: {timestamp}")
      # return[SetSlot(TimeStampInfo, timestamp)]
      return []

#####
# Get current timestamp and more
def get_timestamp():
    url = "https://worldtimeapi.org/api/timezone/Etc/UTC"
    try:
        response = httpx.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("utc_datetime")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e}")
    except httpx.RequestError as e:
        print(f"Request error: {e}")