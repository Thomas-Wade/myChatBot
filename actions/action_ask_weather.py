from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import time
import hashlib
import hmac
import base64
import requests
import json, jsonpath
from urllib import parse

class ActionAskWeather(Action):
    def name(self) -> Text:
        """Unique identifier of the form"""
        return "action_ask_weather"

    def run(self,dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
      response = WeatherInfo.getWeatherData(tracker.get_slot('city'), tracker.get_slot('dateTime'))
      dispatcher.utter_message(response)
      return [{}]

class WeatherInfo:
    KEY = 'S62Exq4yR8Prf20tH'  # API key
    UID = "PKyu9RbGkqJLGp7bG"  # 用户ID
    API = 'https://api.seniverse.com/v3/weather/{dateType}.json'  # API URL，可替换为其他 URL

    @staticmethod
    def getJsonpUrl(location, dateType='now'):
        """通过 HMAC-SHA1 进行签名验证

        需注意，调用最终的 URL 时使用的域名或IP需与当前账号在官网上绑定的域名一致！
        域名绑定可见：http://www.seniverse.com/account
        """
        ts = int(time.time())  # 当前时间戳
        params = "ts={ts}&uid={uid}".format(ts=ts, uid=WeatherInfo.UID)  # 构造验证参数字符串

        key = bytes(WeatherInfo.KEY, 'UTF-8')
        raw = bytes(params, 'UTF-8')

        # 使用 HMAC-SHA1 方式，以 API 密钥（key）对上一步生成的参数字符串（raw）进行加密
        digester = hmac.new(key, raw, hashlib.sha1).digest()

        # 将上一步生成的加密结果用 base64 编码，并做一个 urlencode，得到签名sig
        signature = base64.encodebytes(digester).rstrip()
        sig = parse.quote(signature.decode('utf8'))

        # 构造最终请求的 url
        url = WeatherInfo.API.format(dateType=dateType) + "?location={}&".format(location) + \
              params + '&sig=' + sig + "&callback=?"
        return url

    @staticmethod
    def getWeatherData(location, date='现在'):
        dateList = ['今天', '明天', '后天']
        dateType = 'now' if date == '现在' else 'daily'
        url = WeatherInfo.getJsonpUrl(location, dateType)
        result = requests.get(url)
        text = result.text.strip('?();')
        reponse_json = json.loads(text, encoding='utf-8')
        if dateType == 'now':
            result = jsonpath.jsonpath(reponse_json, '$..now')[0]
            return WeatherInfo.convertJson2SentenceNow(location, result)
        else:
            result = jsonpath.jsonpath(reponse_json, '$..daily')[0]
            index = dateList.index(date)
            return WeatherInfo.convertJson2SentenceDate(location, result[index])

    @staticmethod
    def convertJson2SentenceNow(location, weatherDict):
        return '{location}当前天气{text},温度{temperature}度'.format(
            location=location, **weatherDict)

    @staticmethod
    def convertJson2SentenceDate(location, weatherDict):
        return '{location}{date}，天气{text_day}，最高温度{high}度，' \
               '最低温度{low}度，{wind_direction}风{wind_scale}级，相对湿度{humidity}'\
            .format(location=location, **weatherDict)


if __name__ == '__main__':
    result = WeatherInfo.getWeatherData('太原', '今天')
    print(result)