from envelope import env
import json
import random
from http_wrapper import http_adapter, http_request, http_response, api_wrapper, conn, cred
import http
import sys

class WebServerErr(Exception):
	def __init__(self, code, body):
		self.err = {"status": code, "response": body}
			
	def __str__(self):
		return json.dumps(self.err)

class ZabbixErr(WebServerErr):
	def __init__(self, body):
		self.err = body

class InvalidRequestErr(ZabbixErr):
	pass	
class LoginErr(ZabbixErr):
	pass
class TokenExpirationErr(ZabbixErr):
	pass	

class zbx_http(http_adapter):
	def __init__(self, host, port, user, password, token: str):
		self._connection = conn(host, port)
		self._credentials = cred(user, password, token)

		self._request = http_request({}, {})
		self._request.headers = {"Content-Type": "application/json-rpc"}
		self._request.body = {}
		self._request.path = "/api_jsonrpc.php"

		self._response = http_response()			

	@staticmethod
	def uniqid() -> int:
		return random.randrange(10000, 100000)	

	def set(self, method: str, data: dict):
		self._request.headers["Authorization"] = "Bearer {}".format(self._credentials.token)

		self._request.body = {
			"jsonrpc": "2.0",
			"method": method,
			"params": data,
			"id": self.uniqid()
		}

	def send(self, method: str) -> http_response:
		http_conn = http.client.HTTPConnection(self._connection.host, \
							int(self._connection.port), timeout=30)
		http_conn.request(method, self._request.path, \
						json.dumps(self._request.body), self._request.headers)
		self._response = http_response(http_conn.getresponse())
		http_conn.close()	
		self.__error_check()

	def clear(self):
		self._request = http_request()
		self._request.headers = {"Content-Type": "application/json-rpc"}
		self._request.body = {}
		self._request.path = "/api_jsonrpc.php"

		self._response = http_response()			

	def __error_check(self):
		err = {}

		if self._response.status != 200:
			raise WebServerErr(self._response.status, self._response.body)
		else:
			err = self._response.body.get("error")  
			if err != None:
				if err["code"] == -32500:
					raise LoginErr(err)
				elif err["code"] == -32602:
					raise TokenExpirationErr(err)
				else:
					raise InvalidRequestErr(err)
	
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
		return self._response


class zabbix(api_wrapper):
	necessary = ["zbx_host", "zbx_port", "zbx_user", "zbx_password"]
	
	def __init__(self, input_data: dict | None = None):
		env_file = None

		if input_data == None:
			env_file = env()
			input_data = env_file.content

		self.input_validate(input_data)
		self._http = zbx_http(input_data["zbx_host"], input_data["zbx_port"], \
		input_data["zbx_user"], input_data["zbx_password"],\
		input_data.get("zbx_token"))

		self.server_validate()
		self.user_validate()

		if env_file != None:
			input_data["zbx_token"] = self._http.credentials.token
			env_file.set_content(input_data)

	def login(self):
		self._http._request.body = {
			"jsonrpc": "2.0",
			"method": "user.login",
			"params": {
				"username": self._http.credentials.user,
				"password": self._http.credentials.password
			},
			"id": self._http.uniqid()
		}
		
		self._http.send("POST")

		self._http.credentials.token = self._http._response.body["result"]
		self._http.clear()
	
	def auth(self) -> bool:
		status = bool
		buf = {}

		self._http._request.body = {
			"jsonrpc": "2.0",
			"method": "user.checkAuthentication",
			"params": {
				"sessionid": self._http.credentials.token 
			},
			"id": self._http.uniqid()
		}
		
		self._http.send("POST")	
		self._http.clear()

		return True

	def method(self, name: str, data = {}):
		result = {}
		self._http.set(name, data);
		
		try:
			self._http.send("POST")
		except TokenExpirationErr as ztee:
			self.auth()
			self._http.set(name, data);
			self._http.send("POST")
		
		result = self._http._response.body["result"].copy()
		self._http.clear()

		return result
	
	@property
	def http(self):
		return self._http	
