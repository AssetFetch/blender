import json
import requests
from enum import Enum
from typing import List,Dict
import bpy

class AF_HttpMethod(Enum):
	"""Represents the HTTP methods used by AssetFetch."""
	GET = 'get'
	POST = 'post'
		

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
	def __init__(self,uri:str,method:AF_HttpMethod,parameters:Dict[str,str] = None):
		self.uri = uri
		self.method = method
		self.parameters = parameters

	def execute(self) -> AF_HttpResponse:
		
		if self.method == AF_HttpMethod.GET:
			response = requests.get(self.uri, params=self.parameters)
		elif self.method == AF_HttpMethod.POST:
			response = requests.post(self.uri, data=self.parameters)
		else:
			raise ValueError(f"Unsupported HTTP method: {self.method}")

		# Create and return AF_HttpResponse
		return AF_HttpResponse(content=response.text, response_code=response.status_code)
	
def initialize():
	pass
