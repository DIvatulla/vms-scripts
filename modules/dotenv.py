import re
import os

def empty(string):
	return (len(string) == 0)

class env_builder:
	__buf = ""

	@staticmethod
	def __read_env(path):
		with open(path, 'r') as file:
			env_builder.__buf = file.read()

		if len(env_builder.__buf) == 0:
			raise Exception("Empty file")
	
	@staticmethod
	def __pass_field(line):
		return empty(line) or (line[0] == '#') 

	@staticmethod
	def __check_field(line):
		field = re.split(r"=", line, 1)
		return ((len(field) == 2) and (not (empty(field[0]) or empty(field[1]))))
		
	@staticmethod
	def parse(path):
		env_builder.__read_env(path)
		current_field = [] 
		content = {};
		
		for line in env_builder.__buf.splitlines():
			if env_builder.__pass_field(line):
				continue
	
			if env_builder.__check_field(line):
				current_field = re.split(r"=", line, 1)	
				content[current_field[0]] = current_field[1]
			else:
				env_builder.__buf = ""
				raise Exception("Invalid field {}".format(line));
				
		del env_builder.__buf 
				
		return content

class env:
	def __init__(self, location: str | None = None):
		if location == None:
			self.location = "{}/.env".format(os.environ.get('PWD'))
		else:
			self.location = location	

		self.content = env_builder.parse(self.location)

	def  __rewrite_env_file(self):
		buf = ""

		for field_name in self.content:
			buf = buf + ("{}={}\n".format(field_name, self.content[field_name])) 	

		with open(self.location, 'w') as f:
			f.write(buf)			

	def set_location(self, location):
		self.location = location
		self.__update()

	def set_content(self, env_dict):
		self.content = env_dict
		self.__rewrite_env_file()

	def __update(self):
		self.content = env_builder.parse(self.location)	
