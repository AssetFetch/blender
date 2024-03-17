import os
import bpy
from typing import List,Dict
from .http import *
from .property import AF_PR_AssetFetch, AF_PR_Component, AF_PR_Implementation, AF_PR_ImportStep

def validate_implementation(implementation:AF_PR_Implementation) -> None:

	implementation.is_valid = True

	validation_messages = []
	
	for comp in implementation.components:
		
		if not comp.file_fetch_download:
			implementation.is_valid = False
			validation_messages.append(f"{comp.name} is missing a 'file_fetch.download' datablock. (Other methods are not yet supported)")
		
		if comp.file_info.extension not in ('.obj','.jpg'):
			implementation.is_valid = False
			validation_messages.append(f"{comp.name} is using the extension '{comp.file_info.extension}' which is currently unsupported.")

	if len(validation_messages) > 0:
		implementation.validation_message = "\n".join(validation_messages)
	else:
		implementation.validation_message = "No complications detected."

def build_import_plan(implementation:AF_PR_Implementation) -> None:

	af : AF_PR_AssetFetch = bpy.context.window_manager.af

	provider_id = af.current_provider_initialization.name
	asset_id = af.current_asset_list.assets[af.current_asset_list_index].name
	implementation_id = af.current_implementation_list.implementations[af.current_implementation_list_index].name

	# Step 1: Find the implementation directory
	if provider_id == "":
		raise Exception("No provider ID to create implementation directory.")
	if asset_id == "":
		raise Exception("No asset ID to create implementation directory.")
	if implementation_id == "":
		raise Exception("No implementation ID to create implementation directory.")
	
	implementation.local_directory = os.path.join(af.download_directory,provider_id)
	implementation.local_directory = os.path.join(implementation.local_directory,asset_id)
	implementation.local_directory = os.path.join(implementation.local_directory,implementation_id)

	implementation.import_steps.add().set_action("directory_create").set_config_value("directory",implementation.local_directory)

	# Step 2: Find the relevant unlocking queries
	required_unlocking_query_ids : set = {}

	for comp in implementation.components:
		if comp.unlock_link.unlock_query_id != "":
			required_unlocking_query_ids.add(comp.unlock_link.unlock_query_id)
	
	for q in required_unlocking_query_ids:
		implementation.import_steps.add().set_action("unlock").set_config_value("query_id",q)

	# Step 3: Plan how to acquire and arrange all files in the asset directory
	# Currently ignoring archives
	for comp in implementation.components:
		if comp.file_fetch_download.uri != "":
			implementation.import_steps.add().set_action("fetch_download").set_config_value("component_id",comp.name)

	# Step 4: Plan how to actually import
	for comp in implementation.components:
		if comp.file_info.behavior == "file_active":
			if comp.file_info.extension == ".obj":
				implementation.import_steps.add().set_action("import_obj_from_local_path").set_config_value("component_id",comp.name)


def execute_import_plan(implementation:AF_PR_Implementation) -> None:
	af = bpy.context.window_manager.af
	
	for step in implementation.import_steps:

		if step.action == "directory_create":
			os.mkdir(step.config.directory)
		
		if step.action == "fetch_download":

			component : AF_PR_Component = implementation.components[step.config.component_id]

			# Prepare query
			uri = component.file_fetch_download.uri
			method = component.file_fetch_download.method
			payload = component.file_fetch_download.payload
			query = AF_HttpQuery(uri=uri,method=method,parameters=payload)

			# Determine target path
			if component.file_info.behavior in ['file_passive','file_active']:
				# Download directly into local dir
				destination = os.path.join(implementation.local_directory,component.file_info.local_path)

