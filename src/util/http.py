import datetime
import json,requests,tempfile,os
import time
import random
import logging
import pathlib
from enum import Enum
from typing import List,Dict
import bpy
import jsonschema

from functools import partial

from .. import SCHEMA_PATH

LOGGER = logging.getLogger("af.util.http")
LOGGER.setLevel(logging.INFO)

class AF_HttpResponse:

	"""Represents a response received from a provider."""
	def __init__(self,raw_response:requests.Response):

		self.content = raw_response.text
		self.response_code = raw_response.status_code
		try:
			self.parsed = json.loads(self.content)
		except Exception as e:
			self.parsed = {}

		raw_response.raise_for_status()
		
		if "meta" in self.parsed and "kind" in self.parsed['meta']:
			kind = self.parsed['meta']['kind']
		else:
			raise Exception("Could not resolve meta.kind for this request.")

		target_schema_path = (SCHEMA_PATH+f"/endpoint/{kind}.json").replace("\\","/")
		target_base_path = SCHEMA_PATH.replace("\\","/")

		if not os.path.exists(target_schema_path):
			raise Exception(f"Kind {kind} is not recognized as an endpoint kind because file {target_schema_path} could not be found.")
		
		LOGGER.info(f"Validating against {target_schema_path} with base path {target_base_path}")
		
		with open(target_schema_path, 'r') as schema_file:
			schema = json.load(schema_file)
			jsonschema.validate(instance=self.parsed,schema=schema,
					resolver=jsonschema.RefResolver(
						referrer=f"file:///{target_schema_path}",
						base_uri=f"file:///{target_schema_path}"
						)	   
					)

class AF_HttpQuery:

	default_headers = {
			"User-Agent":f"blender/{bpy.app.version_string} assetfetch-blender/0.1"
		}

	"""Represents a query that the client sends to the provider"""
	def __init__(self,uri:str,method:str,parameters:Dict[str,str] = None, chunk_size:int = 128 * 1024 * 8):
		self.uri = uri
		if(method in ['get','post']):
			self.method = method
		else:
			LOGGER.exception("unsupported HTTP method detected.")
		self.parameters = parameters

		# Variables for modal operation
		self.stream_handle = None
		self.stream_handle_iter = None
		self.file_handle = None
		self.chunk_size = chunk_size
		self.expected_bytes = None
		self.downloaded_bytes = 0

	def get_download_completeness(self) -> float:

		if self.expected_bytes is None:
			return 0.0
		if self.expected_bytes == 0:
			return 0.0

		progress = min(1.0,float(self.downloaded_bytes) / float(self.expected_bytes))

		return progress


	def execute(self,raise_for_status : bool = False) -> AF_HttpResponse:
		af  = bpy.context.window_manager.af

		LOGGER.info(f"Sending http {self.method} to {self.uri} with payload {self.parameters}")

		headers = AF_HttpQuery.default_headers.copy()
		for header_name in af.current_provider_initialization.provider_configuration.headers.keys():
			headers[header_name] = af.current_provider_initialization.provider_configuration.headers[header_name].value

		if self.method == "get":
			response = requests.get(self.uri, params=self.parameters,headers=headers)
		elif self.method == "post":
			response = requests.post(self.uri,params=self.parameters,headers=headers)
		else:
			raise ValueError(f"Unsupported HTTP method: {self.method}")
		
		LOGGER.debug(f"Received http response: {response.content}")

		if raise_for_status:
			response.raise_for_status()

		# Create and return AF_HttpResponse
		return AF_HttpResponse(response)
	
	def execute_as_file_piecewise_start(self,destination_path : str):

		# Check for existing initialization
		if self.stream_handle is not None or self.file_handle is not None:
			raise Exception("Download has already been started.")
		
		# Create helpful variables
		af = bpy.context.window_manager.af

		# Prepare headers for request
		headers = AF_HttpQuery.default_headers.copy()
		for header_name in af.current_provider_initialization.provider_configuration.headers.keys():
			headers[header_name] = af.current_provider_initialization.provider_configuration.headers[header_name].value

		# Open the file handle
		self.file_handle = open(destination_path,'wb')

		# Open the http stream handle
		if self.method == "get":
			self.stream_handle = requests.get(url=self.uri,data=self.parameters,headers=headers,stream=True)
		elif self.method == "post":
			self.stream_handle = requests.post(url=self.uri,data=self.parameters,headers=headers,stream=True)
		else:
			raise ValueError("Unsupported HTTP method.")
	
		self.stream_handle.raise_for_status()
		
		# Try to get the expected bytes
		self.expected_bytes = int(self.stream_handle.headers.get('Content-Length', 0))
		LOGGER.info(f"Opened stream, expecting {self.expected_bytes} bytes.")

		self.downloaded_bytes = 0
		self.stream_handle_iter = self.stream_handle.iter_content(chunk_size=self.chunk_size)

	def execute_as_file_piecewise_next_chunk(self) -> bool:
		if self.stream_handle is None or self.file_handle is None:
			raise Exception("Download has not been initialized")
		
		try:
			chunk = next(self.stream_handle_iter,False)
			if chunk:
				self.file_handle.write(chunk)
				self.downloaded_bytes += len(chunk)
				return True
			else:
				return False
		except Exception as e:
			self.execute_as_file_piecewise_finish()
			raise e

	def execute_as_file_piecewise_finish(self):
		if self.stream_handle is None or self.file_handle is None:
			raise Exception("Download has not been initialized")
		
		self.stream_handle.close()
		self.file_handle.close()
		LOGGER.debug("Closed streams.")

	def execute_as_file(self, destination_path: str) -> None:

		self.execute_as_file_piecewise_start(destination_path)
		
		# Pull all data in one loop
		data_remaining = True
		while data_remaining:
			data_remaining = self.execute_as_file_piecewise_next_chunk()
