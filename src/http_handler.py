import json
import requests
from enum import Enum
from typing import List,Dict
import bpy

class AF_HttpMethod(Enum):
	GET = 'GET'
	POST = 'POST'
	PUT = 'PUT'
	DELETE = 'DELETE'
	PATCH = 'PATCH'
	HEAD = 'HEAD'
	OPTIONS = 'OPTIONS'

	def property_group_items():
		http_methods = []
		for method in AF_HttpMethod._member_names_:
			http_methods.append((method,method,method))
		return http_methods
		

class AF_HttpResponse:
	"""Represents a response received from a server"""
	def __init__(self,content:str,response_code:int):

		self.content = content
		self.response_code = response_code

	def is_ok(self):
		return self.response_code == 200
	
	def parsed_json(self):
		return json.loads(self.content)

class AF_HttpQuery:
	def __init__(self,uri:str,method:AF_HttpMethod,parameters:Dict[str,str] = None):
		self.uri = uri
		self.method = method
		self.parameters = parameters

	def execute(self) -> AF_HttpResponse:
		
		if self.method == AF_HttpMethod.GET:
			response = requests.get(self.uri, params=self.parameters)
		elif self.method == AF_HttpMethod.POST:
			response = requests.post(self.uri, data=self.parameters)
		elif self.method == AF_HttpMethod.PUT:
			response = requests.put(self.uri, data=self.parameters)
		elif self.method == AF_HttpMethod.DELETE:
			response = requests.delete(self.uri)
		elif self.method == AF_HttpMethod.PATCH:
			response = requests.patch(self.uri, data=self.parameters)
		elif self.method == AF_HttpMethod.HEAD:
			response = requests.head(self.uri)
		elif self.method == AF_HttpMethod.OPTIONS:
			response = requests.options(self.uri)
		else:
			raise ValueError(f"Unsupported HTTP method: {self.method}")

		# Create and return AF_HttpResponse
		return AF_HttpResponse(content=response.text, response_code=response.status_code)
	
def initialize():
	pass
