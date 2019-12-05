import time
import hashlib
import hmac
import base64
import requests
import json, jsonpath
from urllib import parse


class WeatherInfo:
    KEY = 'S62Exq4yR8Prf20tH'  # API key
    UID = "PKyu9RbGkqJLGp7bG"  # 用户ID
    API = 'https://api.seniverse.com/v3/weather/{dateType}.json'  # API URL，可替换为其他 URL


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

def dateToIndex(date):
    dateList = ['今天', '明天', '后天']
    return dateList.index(date)


def getWeatherData(location, date='现在'):
    dateType = 'now' if date == '现在' else 'daily'
    url = getJsonpUrl(location, dateType)
    result = requests.get(url)
    text = result.text.strip('?();')
    reponse_json = json.loads(text, encoding='utf-8')
    if date == '现在':
        result = jsonpath.jsonpath(reponse_json, '$..now')[0]
    else:
        result = jsonpath.jsonpath(reponse_json, '$..daily')[0]
        index = dateToIndex(date)
        result = result[index]
    return result


if __name__ == '__main__':
    result = getWeatherData('太原', '明天')
    print(result)
