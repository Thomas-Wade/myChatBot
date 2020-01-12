## contain city
* ask_weather{"city": "北京"}
  - utter_answer

## lack city
* ask_weather
  - utter_ask_city
* info{"city": "北京"}
  - utter_answer

## goodbye story
* goodbye
  - utter_goodbye

## greet story
* greet
  - utter_greet