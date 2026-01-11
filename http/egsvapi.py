from envelope import env
import json
import random
from http_wrapper import http_adapter, http_request, http_response, api_wrapper, conn, cred
import http
import sys

class WebServerErr(Exception):
	def __init__(self, res: http_response):
		self.err = {
			"status": res.status, 
			"response": json.dumps(res.body, ensure_ascii=False)
		}
	
	def __str__(self):
		return json.dumps(self.err)
	
class InvalidRequestErr(WebServerErr):
	pass
class LoginErr(WebServerErr):
	pass
class TokenExpirationErr(WebServerErr):
	pass

class egsv_http(http_adapter):
	def __init__(self, host, port, user, password, token: str):
		self._connection = conn(host, port)
		self._credentials = cred(user, password, token)

		self._request = http_request({}, {})
		self._request.headers = {"Content-Type": "application/json"}
		self._request.body = {}
		self._request.path = "/v2/"

		self._response = http_response()

	def set(self, method: str, data: dict):
		self._request.path = "/v2/{}".format(method)
		self._request.headers["Authorization"] = "Bearer {}".format(self._credentials.token)
		self._request.body = data			

	def send(self, method: str):
		http_conn = http.client.HTTPConnection(self._connection.host, \
							int(self._connection.port), timeout=30)
		http_conn.request(method, self._request.path, json.dumps(self._request.body), self._request.headers)
		self._response = http_response(http_conn.getresponse())
		http_conn.close()	
		self.__error_check()

	def clear(self):
		self._request = http_request()
		self._request.headers = {"Content-Type": "application/json"}
		self._request.path = "/v2/"
		self._response = http_response()

	def __error_check(self):
		if self._response.status != 200:
			match (self._response.body.get("auth_error")):
				case "invalid signature":
					raise TokenExpirationErr(self._response)	
				case "wrong credetenials":
					raise LoginErr(self._response)	
				case _:
					print(self._response.body)
					raise InvalidRequestErr(self._response)

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
		self._http = egsv_http(input_data["egsv_host"], input_data["egsv_port"], \
		input_data["egsv_user"], input_data["egsv_password"], \
		input_data.get("egsv_token"))

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
			}
		}
		self._http.send("POST")
		self._http.credentials.token = self._http._response.body["token"]
		self._http.clear()
	
	def auth(self) -> bool:
		self._http._request.path = "/v2/account.login_with_token"
		self._http._request.body = {
			"auth": {
				"token": self._http._credentials.token
			}
		}

		try:
			self._http.send("POST")
		except LoginErr:
			self._http.clear()
			return False
			
		self._http.clear()
		return True	

	def method(self, name: str, data: dict = {}):
		result = {}
		self._http.set(name, data)

		try:
			self._http.send("POST")
		except TokenExpirationErr:
			self.auth()
			self._http.set(name, data)
			self._http.send("POST")

		result = self._http._response.body.copy()
		self._http.clear()

		return result		

	@property
	def http(self):
		return self._http	
