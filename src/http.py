import json,requests,tempfile
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
		if(method in ['get','post']):
			self.method = method
		else:
			raise Exception("Unsupported HTTP method detected.")
		self.parameters = parameters

	def execute(self) -> AF_HttpResponse:
		af : AF_PR_AssetFetch = bpy.context.window_manager.af

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
	
	def execute_as_temporary_file(self) -> tempfile.NamedTemporaryFile:
		if self.method == 'get':
			response = requests.get(self.uri, params=self.parameters)
		elif self.method == 'post':
			response = requests.post(self.uri, data=self.parameters)
		else:
			raise ValueError("Unsupported HTTP method.")

		# Raise an exception for bad responses
		response.raise_for_status()

		# Create a temporary file to store the downloaded content
		temp_file = tempfile.NamedTemporaryFile(delete=True)

		# Write the downloaded content into the temporary file
		temp_file.write(response.content)
		temp_file.seek(0)  # Reset file pointer to the beginning

		return temp_file