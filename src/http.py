import json
import requests
from enum import Enum
from typing import List,Dict
import bpy

class AF_HttpResponse:
	"""Represents a response received from a provider."""
	def __init__(self,content:str,response_code:int):

		self.content = content
		self.response_code = response_code
		self.parsed = json.loads(content)

	def is_ok(self):
		return self.response_code == 200

class AF_HttpQuery:
	"""Represents a query that the client sends to the provider"""
	def __init__(self,uri:str,method:str,parameters:Dict[str,str] = None):
		self.uri = uri
		self.method = method
		self.parameters = parameters

	def execute(self) -> AF_HttpResponse:
		af = bpy.context.window_manager.af

		headers = {}
		for header_name in af.current_provider_initialization.provider_configuration.headers.keys():
			headers[header_name] = af.current_provider_initialization.provider_configuration.headers[header_name].value

		if self.method == "get":
			response = requests.get(self.uri, params=self.parameters,headers=headers)
		elif self.method == "post":
			response = requests.post(self.uri, data=self.parameters)
		else:
			raise ValueError(f"Unsupported HTTP method: {self.method}")

		# Create and return AF_HttpResponse
		return AF_HttpResponse(content=response.text, response_code=response.status_code)
	
def initialize():
	pass
