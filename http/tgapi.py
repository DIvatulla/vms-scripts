from envelope import env
import json
import random
from http_wrapper import http_request, http_response, api_wrapper, conn, cred
import http
import sys
import re

class tg_http():
	def __init__(self, token: str):
		self.connection = conn("api.telegram.org", 443)
		self.credentials = cred("", "", token)

		self.request = http_request({"Content-Type": "application/json"})
		self.request.path = "/bot{}/".format(token)

		self.response = None

	def send(self, method: str) -> http_response:
		http_conn = http.client.HTTPSConnection(self.connection.host, \
							self.connection.port, timeout=30)
		http_conn.request(method, self.request.path, \
						json.dumps(self.request.body), self.request.headers)
		self.response = http_response(http_conn.getresponse())
		http_conn.close()	

		self.request.headers = {"Content-Type": "application/json"}
		self.request.body = {}

class bot():
	def __init__(self):
		self.https = tg_http(env().content["bot_token"])
		self.chat_id = env().content["chat_id"]

	def send_msg(self, text: str) -> http_response:
		tmp = self.https.request.path

		self.https.request.path += "sendMessage"
		self.https.request.body = {
			"chat_id": self.chat_id,
			"text": self.mdformat(text),
			"parse_mode": "MarkdownV2"
		}
		print(self.https.request.body)
		self.https.send("POST")
		self.https.request.path = tmp
		
		if self.https.response.status != 200:
			raise Exception({"status": self.https.response.status, \
							"response": self.https.response.body})

		return self.https.response

	@staticmethod
	def mdformat(s: str) -> str:
		escape_chars = r"\[]()~>+-=|{}.!"
		return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", s)
