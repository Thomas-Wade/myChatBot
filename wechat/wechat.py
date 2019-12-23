# The Silly Echo Bot for WeChat - Python version
#
# The purpose of this code is to show the basics of creating chatbots for the WeChat platform.
# It creates a simple backend that echoes back the messages it receives from users.
#
# See my article on Chatbots Magazine for details:
# https://chatbotsmagazine.com/building-chatbots-for-wechat-part-1-dba8f160349
#
# Tested with:
# Python 3.5.2
# Gunicorn 19.7.0 - http://gunicorn.org
# Falcon 1.1.0 - https://falconframework.org
# xmltodict 0.10.2 - https://github.com/martinblech/xmltodict
#
# Try it on a sandbox account: http://admin.wechat.com/debug/sandbox
# Works well with ngrok for local testing: https://ngrok.com
#
# License: MIT (https://opensource.org/licenses/MIT) (C) Edoardo Nosotti, 2017

# Import dependencies
import hashlib
import time
import falcon
import xmltodict
import requests, json

# Set the shared token (must be set in the WeChat sandobox console, too)
WECHAT_TOKEN = "wechat_token"

# See: https://falcon.readthedocs.io/en/stable/user/quickstart.html
class WeChatApiResource(object):
  def __init__(self, token):
    self.token = token

  # Check if the message XML is valid, this simple bot handles TEXT messages only!
  # To learn more about the supported types of messages and how to implement them, see:
  # Common Messages: http://admin.wechat.com/wiki/index.php?title=Common_Messages
  # Event Messages: http://admin.wechat.com/wiki/index.php?title=Event-based_Messages
  # Speech Recognition Messages: http://admin.wechat.com/wiki/index.php?title=Speech_Recognition_Messages
  def validate_message(self, message):
    return (
      message != None and
      message['xml'] != None and
      message['xml']['MsgType'] != None and
      message['xml']['MsgType'] == 'text' and
      message['xml']['Content'] != None
    )

  def get_rasa_reply(self, userId, message):
    url = r'http://rasa:5005/webhooks/rest/webhook'
    headers = {'Content-Type': 'application/json', 'charset': 'UTF-8'}
    body = json.dumps({"sender": userId, "message": message})
    response = requests.post(url, body, headers=headers)
    reponse_json = json.loads(response.text, encoding='utf-8')
    return reponse_json[0]['text']

  # Format the reply according to the WeChat XML format for synchronous replies,
  # see: http://admin.wechat.com/wiki/index.php?title=Callback_Messages
  def format_message(self, original_message, content):
    return (
      "<xml>"
      "<ToUserName><![CDATA[%s]]></ToUserName>"
      "<FromUserName><![CDATA[%s]]></FromUserName>"
      "<CreateTime>%s</CreateTime>"
      "<MsgType><![CDATA[text]]></MsgType>"
      "<Content><![CDATA[%s]]></Content>"
      "</xml>"
    ) % (
      original_message['xml']['FromUserName'], # From and To must be inverted in replies ;)
      original_message['xml']['ToUserName'], # Same as above!
      time.gmtime(),
      content
    )

  # The WeChat server will issue a GET request in order to verify the chatbot backend server upon configuration.
  # See: http://admin.wechat.com/wiki/index.php?title=Getting_Started#Step_2._Verify_validity_of_the_URL
  # and: http://admin.wechat.com/wiki/index.php?title=Message_Authentication
  def on_get(self, request, response):
    # Get the parameters from the query string
    signature = request.get_param('signature')
    timestamp = request.get_param('timestamp')
    nonce = request.get_param('nonce')
    echostr = request.get_param('echostr')

    # Compute the signature (note that the shared token is used too)
    verification_elements = [self.token, timestamp, nonce]
    verification_elements.sort()
    verification_string = "".join(verification_elements)
    verification_string = hashlib.sha1(verification_string.encode('utf-8')).hexdigest()

    # If the signature is correct, output the same "echostr" provided by the WeChat server as a parameter
    if signature == verification_string:
      response.status = falcon.HTTP_200
      response.body = echostr
    else:
      response.status = falcon.HTTP_500
      response.body = ""

  # Messages will be POSTed from the WeChat server to the chatbot backend server,
  # see: http://admin.wechat.com/wiki/index.php?title=Common_Messages
  def on_post(self, request, response):
    # Parse the WeChat message XML format
    message = xmltodict.parse(request.bounded_stream.read())

    # If the message is valid, echo it back to the user or send an error message.
    # Some kind of response, even an empty one, is *REQUIRED* by WeChat
    # within the mandatory timeout limit of 5 seconds.
    # Otherwise, the user will see an error in the app.
    if self.validate_message(message):
      reply = self.get_rasa_reply(message['xml']['FromUserName'], message['xml']['Content'])
      response.status = falcon.HTTP_200
      response.body = self.format_message(message, reply)
    else:
      response.status = falcon.HTTP_200
      response.body = "Message was sent in a wrong format."

# Init Falcon
api = application = falcon.API()

# Map a route (see: https://falcon.readthedocs.io/en/stable/api/api.html#falcon.API.add_route)
api.add_route('/wechat', WeChatApiResource(WECHAT_TOKEN))
