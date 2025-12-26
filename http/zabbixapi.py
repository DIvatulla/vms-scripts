from dotenv import env
import json
import random
from http_wrapper import http_adapter, http_request, http_response, api_wrapper, conn, cred
import http

class zbx_http(http_adapter):
	def __init__(self, host, port, user, password, token: str):
		self._connection = conn(host, port)
		self._credentials = cred(user, password, token)

		self._request = http_request()

		self._request.headers = {"Content-Type": "application/json-rpc"}
		self._request.body = {}
		self._request.path = "/api_jsonrpc.php"

		self._response = None

	@staticmethod
	def uniqid() -> int:
		return random.randrange(10000, 100000)	

	def send(self, method: str) -> http_response:
		http_conn = http.client.HTTPConnection(self._connection.host, \
							int(self._connection.port), timeout=30)
		self._request.body["id"] = self.uniqid()
		http_conn.request(method, self._request.path, \
						json.dumps(self._request.body), self._request.headers)
		self._response = http_response(http_conn.getresponse())
		http_conn.close()	

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
		self._http.request.body = {
			"jsonrpc": "2.0",
			"method": "user.login",
			"params": 
			{
				"username": self._http.credentials.user,
				"password": self._http.credentials.password
			},
			"id": self._http.uniqid()
		}

		self._http.send("POST")
		self._http.credentials.token = self._http._response.body["result"]
	
	def auth(self) -> bool:
		self._http._request.body = {
			"jsonrpc": "2.0",
			"method": "user.checkAuthentication",
			"params":
			{
				"sessionid": self._http.credentials.token
			},
		}

		self._http.send("POST")

		return self._http._response.status == 200 	

	def method(self, method_name: str, data = {}):
		self._http._request.headers["Authorization"] = \
			"Bearer {}".format(self._http._credentials.token)

		self._http._request.body = {
			"jsonrpc": "2.0",
			"method": method_name,
			"params": [data],
		}

		self._http.send("POST")
		
		if self._http._response.status != 200:# if nginx is gonna act strange
			raise Exception({"status": self._http._response.status, \
							"response": self._http._response.body})
		if (self._http._response.body.get("error") != None) and \
			(self._http._response.body["error"]["code"] == -32602):# if token expired
			self.login()
			self._http.send("POST")

		return self._http._response.body

	@property
	def http(self):
		return self._http	
