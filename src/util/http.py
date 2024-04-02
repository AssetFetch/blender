import json,requests,tempfile,os
import pathlib
from enum import Enum
from typing import List,Dict
import bpy
import jsonschema

from .. import SCHEMA_PATH

class AF_HttpResponse:

	"""Represents a response received from a provider."""
	def __init__(self,raw_response:requests.Response):

		self.content = raw_response.text
		self.response_code = raw_response.status_code
		self.parsed = json.loads(self.content)

		raw_response.raise_for_status()
		
		try:
			kind = self.parsed['meta']['kind']
		except Exception as e:
			raise Exception("Could not resolve meta.kind for this request.")

		target_schema_path = (SCHEMA_PATH+f"/endpoint/{kind}.json").replace("\\","/")
		target_base_path = SCHEMA_PATH.replace("\\","/")

		if not os.path.exists(target_schema_path):
			raise Exception(f"Kind {kind} is not recognized as an endpoint kind because file {target_schema_path} could not be found.")
		
		print(f"Validating against {target_schema_path} with base path {target_base_path}...")
		
		with open(target_schema_path, 'r') as schema_file:
			schema = json.load(schema_file)
			jsonschema.validate(instance=self.parsed,schema=schema,
					   resolver=jsonschema.RefResolver(
						   referrer=f"file:///{target_schema_path}",
						   base_uri=f"file:///{target_schema_path}"
						)	   
					)
			
		print("... Validation OK") 


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
		af  = bpy.context.window_manager.af

		print(f"sending http {self.method} to {self.uri} with {self.parameters}")

		headers = {}
		for header_name in af.current_provider_initialization.provider_configuration.headers.keys():
			headers[header_name] = af.current_provider_initialization.provider_configuration.headers[header_name].value

		if self.method == "get":
			response = requests.get(self.uri, params=self.parameters,headers=headers)
		elif self.method == "post":
			response = requests.post(self.uri,params=self.parameters,headers=headers)
		else:
			raise ValueError(f"Unsupported HTTP method: {self.method}")

		# Create and return AF_HttpResponse
		return AF_HttpResponse(response)
	
	def execute_as_temporary_file(self) -> tempfile.NamedTemporaryFile:
		"""This method is only used for small media files, such as thumbnails."""
		af = bpy.context.window_manager.af

		headers = {}
		for header_name in af.current_provider_initialization.provider_configuration.headers.keys():
			headers[header_name] = af.current_provider_initialization.provider_configuration.headers[header_name].value

		if self.method == 'get':
			response = requests.get(self.uri, params=self.parameters,headers=headers)
		elif self.method == 'post':
			response = requests.post(self.uri, data=self.parameters,headers=headers)
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
	
	def execute_as_file(self, destination_path: str) -> None:

		af = bpy.context.window_manager.af

		headers = {}
		for header_name in af.current_provider_initialization.provider_configuration.headers.keys():
			headers[header_name] = af.current_provider_initialization.provider_configuration.headers[header_name].value

		try:
			file_handle = open(destination_path,'wb')

			if self.method == "get":
				stream_handle = requests.get(url=self.uri,data=self.parameters,headers=headers,stream=True)
			elif self.method == "post":
				stream_handle = requests.post(url=self.uri,data=self.parameters,headers=headers,stream=True)
			else:
				raise ValueError("Unsupported HTTP method.")
		
			stream_handle.raise_for_status()

			for chunk in stream_handle.iter_content(4096):
				if chunk:
					file_handle.write(chunk)
			
		finally:
			stream_handle.close()
			file_handle.close()
		