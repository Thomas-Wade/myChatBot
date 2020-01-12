from rasa_sdk import Action
from rasa_sdk.events import SlotSet


class ActionAskWeather(Action):
    def name(self) -> Text:
        """Unique identifier of the form"""
        return "action_ask_weather"

    def run(self,
           dispatcher: CollectingDispatcher,
           tracker: Tracker,
           domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

      cuisine = tracker.get_slot('cuisine')
      q = "select * from restaurants where cuisine='{0}' limit 1".format(cuisine)
      result = db.query(q)

      return [SlotSet("matches", result if result is not None else [])]
