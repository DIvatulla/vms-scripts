from dotenv import env
import json
import random
from http_wrapper import http_adapter, http_request, http_response, api_wrapper, conn, cred
import http
import sys

class egsv_http(http_adapter):
	def __init__(self, host, port, user, password, token: str):
		self._connection = conn(host, port)
		self._credentials = cred(user, password, token)

		self._request = http_request()

		self._request.headers = {"Content-Type": "application/json"}
		self._request.body = {}
		self._request.path = "/v2/"

		self._response = None

	def send(self, method: str) -> http_response:
		http_conn = http.client.HTTPConnection(self._connection.host, \
							int(self._connection.port), timeout=30)
		http_conn.request(method, self._request.path, json.dumps(self._request.body), self._request.headers)
		self._response = http_response(http_conn.getresponse())
		http_conn.close()	

		self._request.headers = {"Content-Type": "application/json"}
		self._request.body = {}

	@property
	def connection(self):
		return self._connection

	@property
	def credentials(self):
		return self._credentials

	@property
	def request(self):
		return self._request

	@property
	def response(self):
		return self._request


class egsv(api_wrapper):
	necessary = ["egsv_host", "egsv_port", "egsv_user", "egsv_password"]
	
	def __init__(self, input_data: dict | None = None):
		env_file = None

		if input_data == None:
			env_file = env()
			input_data = env_file.content

		self.input_validate(input_data)
		self._http = egsv_http(input_data["egsv_host"], input_data["egsv_port"], input_data["egsv_user"], input_data["egsv_password"], input_data.get("egsv_token"))

		self.server_validate()
		self.user_validate()

		if env_file != None:
			input_data["egsv_token"] = self._http.credentials.token
			env_file.set_content(input_data)

	def login(self):
		self._http._request.path = "/v2/account.login"
		self._http._request.body = {
			"auth": {
				"username": self._http.credentials.user,
				"password": self._http.credentials.password
			},
		}
		self._http.send("POST")
		self._http.credentials.token = self._http._response.body["token"]
	
	def auth(self) -> bool:
		self._http._request.path = "/v2/account.login_with_token"
		self._http._request.body = {
			"auth": {
				"token": self._http._credentials.token
			}
		}
		self._http.send("POST")

		return self._http._response.status == 200 	

	def method(self, method_name: str, data = {}):
		self._http._request.path = "/v2/{}".format(method_name)
		self._http._request.headers["Authorization"] = \
			"Bearer {}".format(self._http._credentials.token)
		self._http._request.body = data			

		self._http.send("POST")
		
		if self._http._response.status != 200:
			raise Exception({"status": self._http._response.status, \
							"response": self._http._response.body})

		return self._http._response.body

	@property
	def http(self):
		return self._http	
