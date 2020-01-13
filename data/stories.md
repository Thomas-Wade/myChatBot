## contain city
* ask_weather{"city": "北京"}
  - action_ask_weather

## lack city
* ask_weather
  - utter_ask_city
* info{"city": "北京"}
  - action_ask_weather

## goodbye story
* goodbye
  - utter_goodbye

## greet story
* greet
  - utter_greet