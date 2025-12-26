from dotenv import env
import json
import random
from http_wrapper import http_adapter, http_request, http_response, api_wrapper, conn, cred
import http
import sys

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
			"params": [data],
			"id": self.uniqid()
		}

	def send(self, method: str) -> http_response:
		http_conn = http.client.HTTPConnection(self._connection.host, \
							int(self._connection.port), timeout=30)
		http_conn.request(method, self._request.path, \
						json.dumps(self._request.body), self._request.headers)
		self._response = http_response(http_conn.getresponse())
		http_conn.close()	

	def clear(self):
		self._request = http_request()
		self._request.headers = {"Content-Type": "application/json-rpc"}
		self._request.body = {}
		self._request.path = "/api_jsonrpc.php"

		self._response = http_response()			
	
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
		self._http = zbx_http(input_data["zbx_host"], input_data["zbx_port"], input_data["zbx_user"], input_data["zbx_password"], input_data.get("zbx_token"))

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
		self.__error_check()

		self._http.credentials.token = self._http._response.body["result"]
		self._http.clear()
	
	def auth(self) -> bool:
		status = bool

		self._request.body = {
			"jsonrpc": "2.0",
			"method": "user.checkAuthentication",
			"params": {
				"sessionid": self._http.credentials.token 
			},
			"id": self._http.uniqid()
		}
		
		try:	
			self.__error_check()
		except:
			return false
		finally:
			self._http.clear()

		return true

	def method(self, name: str, data = {}):
		result = {}
		self._http.set(name, data);
		self._http.send("POST")
		
		result = self._http._response.body["result"].copy()
		self._http.clear()

		return result
	
	def __error_check(self):
		if self._http._response.status != 200:# if nginx is gonna act strange
			raise Exception({"status": self._http._response.status, \
							"response": self._http._response.body})
		if self._http._response.body.get("error") != None:
			raise Exception(self._http._response.body["error"])
	
	@property
	def http(self):
		return self._http	
