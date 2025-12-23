import sys
sys.path.append("../modules/")
import list_operations
from abc import ABC, abstractmethod
import http.client
import subprocess
import json
import re

def ping(address: str):
	result = subprocess.run(['ping', '-c', '1', '-W', '10', address], stdout=subprocess.PIPE)
	return result.returncode == 0

class http_request:
	def __init__(self, headers: dict = {}, body: dict = {}):
		self.path = "/"
		self.headers = headers
		self.body = body

class http_response:
	def __init__(self, response: http.client.HTTPResponse):
		self.headers = {}
		self.status = response.status
		self.body = json.loads(response.read().decode())
		self.__parse_headers(response.headers)

	def __parse_headers(self, message: http.client.HTTPMessage):
		buf = []

		for line in re.split(r"\n", message.as_string()):
			if len(line) < 1:
				continue
			buf = re.split(r": ", line, 1)
			self.headers[buf[0]] = buf[1]

class conn:
	def __init__(self, host, port: str):
		self.host = host
		self.port = int(port)

class cred:
	def __init__(self, user, password, token: str):
		self.user = user
		self.password = password
		self.token = token

class http_adapter(ABC):
	@property
	@abstractmethod
	def credentials(self) -> cred:
		pass

	@property
	@abstractmethod
	def connection(self) -> conn:
		pass

	@abstractmethod
	def send(self):
		pass

	@property
	@abstractmethod
	def request(self):
		return http_request()	

	@property
	@abstractmethod
	def response(self):
		return http_response()	

	@property
	@abstractmethod
	def credentials(self):
		return cred()	

	@property
	@abstractmethod
	def connection(self):
		return conn() 

class api_wrapper(ABC):
	@staticmethod
	@property
	@abstractmethod
	def necessary(self) -> list:
		return []
	
	@property
	@abstractmethod
	def http(self) -> http_adapter:
		pass

	@abstractmethod
	def login(self):
		pass

	@abstractmethod
	def auth(self):
		pass

	@abstractmethod
	def method(self):
		pass

	def input_validate(self, input_data: list):
		diff = list_operations.differ(self.necessary, \
		(list_operations.intersect(input_data, self.necessary)))

		if len(diff) != 0:
			raise Exception("Env file has no {} fields".format(str(diff)))

	def server_validate(self):
		if not ping(self.http.connection.host):
			raise Exception("{} is unreacheable".format(self._host))

	def user_validate(self):
		if self.http.credentials.token == None:
			self.login()
		elif not(self.auth()):
			raise Exception("{} invalid token".format(self._http.token))
