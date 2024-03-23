import glob
import hashlib
import json
import os
import bpy,math,tempfile
import bpy_extras.image_utils
from typing import Dict,List

from src.property import AF_PR_AssetFetch, AF_PR_Component, AF_PR_Implementation
from . import http

# Utility functions

def dict_to_attr(source:Dict[str,str],keys:List[str],destination:any):
	"""Assigns all the provided keys from source as attributes to the destination object."""
	for key in keys:
		if key in source:
			setattr(destination,key,source[key])

# Registration and unregistration functions
	
def register():
	for cl in registration_targets:
		bpy.utils.register_class(cl)

def unregister():
	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)

# Operator definitions

class AF_OP_InitializeProvider(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.initialize_provider"
	bl_label = "Initialize Provider"
	bl_options = {"REGISTER"}

	#url: StringProperty(name="URL")

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):
		af : AF_PR_AssetFetch = bpy.context.window_manager.af

		# Reset existing connection_state
		if 'current_provider_initialization' in af:
			af['current_provider_initialization'].clear()

		if 'current_connection_state' in af:
			af['current_connection_state'].clear()

		if 'current_asset_list' in af:
			af['current_asset_list'].clear()

		if 'current_asset_list_index' in af:
			af['current_asset_list_index'] = 0

		if 'current_implementation_list' in af:
			af['current_implementation_list'].clear()

		if 'current_implementation_list_index' in af:
			af['current_implementation_list_index'] = 0


		# Contact initialization endpoint and get the response
		query = http.AF_HttpQuery(uri=af.current_init_url,method="get")
		response : http.AF_HttpResponse = query.execute()

		# Set the provider id
		if "id" in response.parsed:
			af.current_provider_initialization.name = response.parsed['id']
		else:
			raise Exception("No provider ID.")

		# Get the provider text (title and description)
		if "text" in response.parsed['data']:
			af.current_provider_initialization.text.configure(response.parsed['data']['text'])
			
		# Provider configuration
		af.current_provider_initialization.provider_configuration.headers.clear()
		if "provider_configuration" in response.parsed['data']:

			provider_config = response.parsed['data']['provider_configuration']

			# Headers
			if len(provider_config['headers']) > 0:
				af.current_connection_state.state = "awaiting_input"
				for header_info in provider_config['headers']:
					current_header = af.current_provider_initialization.provider_configuration.headers.add()
					dict_to_attr(header_info,['name','default','is_required','is_sensitive','prefix','suffix','title','encoding'],current_header)
					if "default" in header_info:
						current_header.value = header_info['default']
			else:
				af.current_connection_state.state = "connected"

			# Status endpoint
			dict_to_attr(provider_config['connection_status_query'],['uri','method'],af.current_provider_initialization.provider_configuration.connection_status_query)
			for payload_key in provider_config['connection_status_query']['payload']:
				new_payload = af.current_provider_initialization.connection_status_query.payload.add()
				new_payload.name = payload_key
				new_payload.value = provider_config['connection_status_query']['payload'][payload_key]
		else:
			# No configuration required...
			af.current_connection_state.state = "connected"

		# asset_list_query
		if "asset_list_query" in response.parsed['data']:
			af.current_provider_initialization.asset_list_query.configure(response.parsed['data']['asset_list_query'])
		else:
			raise Exception("No Asset List Query!")
		
		return {'FINISHED'}
	
class AF_OP_ConnectionStatus(bpy.types.Operator):
	"""Performs a status query to the provider, if applicable."""

	bl_idname = "af.connection_status"
	bl_label = "Get Connection Status"
	bl_options = {"REGISTER"}

	def execute(self,context):
		af : AF_PR_AssetFetch = bpy.context.window_manager.af

		# Contact initialization endpoint and get the response
		response : http.AF_HttpResponse = af.current_provider_initialization.provider_configuration.connection_status_query.to_http_query().execute()

		# Test if connection is ok
		if response.is_ok():
			af.current_connection_state.state = "connected"

			# Set user data if available
			if "user" in response.parsed['data']:
				dict_to_attr(response.parsed['data']['user'],['display_name','display_tier','display_icon_uri'],af.current_connection_state.user)
			else:
				af.current_connection_state['user'].clear()

			# Set unlock balance if available
			if "unlock_balance" in response.parsed['data']:
				dict_to_attr(response.parsed['data']['unlock_balance'],['balance','balance_unit','balance_refill_url'],af.current_connection_state.unlock_balance)
				af.current_connection_state.unlock_balance.is_set = True
			else:
				af.current_connection_state['unlock_balance'].clear()

		else:
			af.current_connection_state.state = "connection_error"

		

		return {'FINISHED'}

class AF_OP_UpdateAssetList(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.update_asset_list"
	bl_label = "Update Asset List"
	bl_options = {"REGISTER","UNDO"}

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):
		af : AF_PR_AssetFetch = bpy.context.window_manager.af

		# Contact initialization endpoint
		response = af.current_provider_initialization.asset_list_query.to_http_query().execute()
		
		# Save assets in blender properties
		af.current_asset_list.assets.clear()
		for asset in response.parsed['assets']:
			asset_entry = af.current_asset_list.assets.add()
			asset_entry.name = asset['id']

			# Text
			if "text" in asset['data']:
				asset_entry.text.title = asset['data']['text']['title']
				asset_entry.text.description = asset['data']['text']['title']
			
			# Implementations Query
			if "implementation_list_query" in asset['data']:
				asset_entry.implementation_list_query.configure(asset['data']['implementation_list_query'])

		af.current_asset_list_index = 0

		# Reset implementations list
		af.current_implementation_list.implementations.clear()
		
		return {'FINISHED'}

class AF_OP_UpdateImplementationsList(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.update_implementations_list"
	bl_label = "Update Implementations List"
	bl_options = {"REGISTER","UNDO"}

	#url: StringProperty(name="URL")

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):
		af : AF_PR_AssetFetch = bpy.context.window_manager.af
		current_asset = af.current_asset_list.assets[af.current_asset_list_index]

		# Contact implementations endpoint
		response = current_asset.implementation_list_query.to_http_query().execute()

		# Converting the json response into blender bpy data
		af['current_implementation_list'].clear()

		# Parse the datablocks for the ImplementationList itself

		if "unlock_queries" in response.parsed['data']:
			for unlock_query in response.parsed['data']['unlock_queries']:
				af.current_implementation_list.unlock_queries.add().configure(unlock_query)

		for incoming_impl in response.parsed['implementations']:

			# -------------------------------------------------------------------------------
			# Create a new implementation to fill with data
			current_impl : AF_PR_Implementation = af.current_implementation_list.implementations.add()


			# Enter try-catch block
			# Failing this block causes an implementation to be considered unreadable.
			# If it passes, it is considered readable.
			
			try:
				
				# We start by assuming that the implementation is valid
				current_impl.is_valid = True

				# -------------------------------------------------------------------------------
				# Fill the implementation with data from the HTTP endpoint

				# Implementation id
				if "id" not in incoming_impl:
					raise Exception("Implementation is missing and id.")
				current_impl.name = incoming_impl['id']

				# Component data
				if "components" not in incoming_impl or len(incoming_impl['components']) < 1:
					raise Exception("This implementation has no components.")
				for provider_comp in incoming_impl['components']:
					
					blender_comp = current_impl.components.add()

					# For clarity:
					# provider_comp -> the component data sent by the provider
					# blender_comp -> the blender bpy property this component gets turned into
					# pcd -> shorthand for "provider component data" (This will appear a lot)
					pcd = provider_comp['data']
					
					# Component id
					if "id" not in provider_comp:
						raise Exception("A component is missing an id.")
					blender_comp.name = provider_comp['id']

					recognized_datablock_names = [

						"file_info",
						"file_fetch.download",
						"file_fetch.from_archive",

						"loose_environment",
						"loose_material_define",
						"loose_material_apply",

						"format.blend",
						"format.usd",
						"format.obj",

						"unlock_link",
						"text"
						
						]
					
					# Unsupported datablocks which lead to a warning
					for key in pcd.keys():
						if key not in recognized_datablock_names:
							current_impl.validation_messages.add().set("warn",f"Datablock {key} in {blender_comp.name} has not been recognized and will be ignored.")
					
					# Configure datablocks
					for key in recognized_datablock_names:
						if key in pcd:
							print(f"setting {blender_comp.name} -> {key}")
							block = getattr(blender_comp,key.replace(".","_"))
							block.is_set = True
							block.configure(pcd[key])
						else:
							# Some datablocks are required and get tested for here.
							if key in ['file_info']:
								raise Exception(f"{blender_comp.name} is missing a {key} datablock.")
					
					

				# -------------------------------------------------------------------------------
				# Attempt to build an import plan for the implementation

				# Step 0: Create helpful variables
				provider_id = af.current_provider_initialization.name
				asset_id = af.current_asset_list.assets[af.current_asset_list_index].name
				implementation_id = current_impl.name

				# Step 1: Find the implementation directory
				if provider_id == "":
					raise Exception("No provider ID to create implementation directory.")
				if asset_id == "":
					raise Exception("No asset ID to create implementation directory.")
				if implementation_id == "":
					raise Exception("No implementation ID to create implementation directory.")
				
				current_impl.local_directory = os.path.join(af.download_directory,provider_id)
				current_impl.local_directory = os.path.join(current_impl.local_directory,asset_id)
				current_impl.local_directory = os.path.join(current_impl.local_directory,implementation_id)

				current_impl.import_steps.add().set_action("directory_create").set_config_value("directory",current_impl.local_directory)

				# Step 2: Find the relevant unlocking queries
				required_unlocking_query_ids : set = set()

				for comp in current_impl.components:
					if comp.unlock_link.unlock_query_id != "":
						required_unlocking_query_ids.add(comp.unlock_link.unlock_query_id)
				
				for q in required_unlocking_query_ids:
					current_impl.import_steps.add().set_action("unlock").set_config_value("query_id",q)

				# Step 3: Plan how to acquire and arrange all files in the asset directory
				# TODO Currently ignoring archives
				already_processed_component_ids = set()
				
				def recursive_fetching_datablock_handler(comp : AF_PR_Component):

					# Keep track of which components were already processed
					if comp.name in already_processed_component_ids:
						return
					else:
						already_processed_component_ids.add(comp.name)
					
					# Decide how to handle this component (recursively if it references an archive)
					if comp.file_fetch_download.is_set:
						current_impl.import_steps.add().set_action("fetch_download").set_config_value("component_id",comp.name)
					elif comp.file_fetch_from_archive.is_set:
						target_comp = next(c for c in current_impl.components if c.name == comp.file_fetch_from_archive.archive_component_id)
						if not target_comp:
							raise Exception(f"Referenced component {comp.file_fetch_from_archive.archive_component_id} could not be found.")
						recursive_fetching_datablock_handler(target_comp)
					elif comp.unlock_link.is_set:
						current_impl.import_steps.add().set_action("fetch_download_unlocked").set_config_value("component_id",comp.name)
					else:
						raise Exception(f"{blender_comp.name} is missing either a file_fetch.download, file_fetch.from_archive or unlock_link datablock.")

				for comp in current_impl.components:
					recursive_fetching_datablock_handler(comp)
					

				# Step 4: Plan how to import main model file
				for comp in current_impl.components:
					if comp.file_info.behavior == "file_active":
						if comp.file_info.extension == ".obj":
							current_impl.import_steps.add().set_action("import_obj_from_local_path").set_config_value("component_id",comp.name)
						if comp.file_info.extension in [".usd",".usda",".usdc",".usdz"]:
							current_impl.import_steps.add().set_action("import_usd_from_local_path").set_config_value("component_id",comp.name)

				# Step 5: Plan how to import other active files, such as loose materials
				# List to keep track of which materials have already been created
				already_created_materials = []
				for comp in current_impl.components:
					if comp.loose_material_define.is_set:
						if comp.loose_material_define.material_name not in already_created_materials:
							current_impl.import_steps.add().set_action("material_create").set_config_value("material_name",comp.loose_material_define.material_name)
							already_created_materials.append(comp.loose_material_define.material_name)
						current_impl.import_steps.add().set_action("material_add_map").set_config_value("component_id",comp.name)
					if comp.loose_material_apply.is_set:
						if comp.loose_material_apply.material_name not in already_created_materials:
							current_impl.import_steps.add().set_action("material_create").set_config_value("material_name",comp.loose_material_apply.material_name)
							already_created_materials.append(comp.loose_material_apply.material_name)
						current_impl.import_steps.add().set_action("material_assign").set_config_value("component_id",comp.loose_material_apply.material_name)

			except Exception as e:
				current_impl.is_valid = False
				current_impl.validation_messages.add().set("crit",str(e))
				raise e

		return {'FINISHED'}
	
class AF_OP_ExecuteImportPlan(bpy.types.Operator):
	"""Executes the currently loaded import plan."""
	
	bl_idname = "af.execute_import_plan"
	bl_label = "Execute Import Plan"
	bl_options = {"REGISTER","UNDO"}

	#url: StringProperty(name="URL")

	#def draw(self,context):
	#	pass
		#layout = self.layout
		#layout.prop(self,'radius')

	@classmethod
	def poll(self,context):
		af = bpy.context.window_manager.af
		return len(af.current_implementation_list.implementations) > 0 and af.current_implementation_list.implementations[af.current_implementation_list_index].is_valid
	
	def get_or_create_material(self,material_name:str,asset_id:str):
		if material_name in bpy.data.materials and bpy.data.materials[material_name]['af_managed'] and bpy.data.materials[material_name]['af_asset_id'] == asset_id:
			return bpy.data.materials[material_name]
		new_material= bpy.data.materials.new(name=material_name)
		new_material.use_nodes = True

		# Add principled bsdf and tex coord
		new_material.node_tree.nodes.clear()
		output = new_material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
		bsdf_shader = new_material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
		bsdf_shader.name = "BSDF"
		tex_coord = new_material.node_tree.nodes.new(type='ShaderNodeTexCoord')
		tex_coord.name = "TEX_COORD"

		# Basic links
		new_material.node_tree.links.new(bsdf_shader.outputs['BSDF'],output.inputs['Surface'])

		# Mark as AF
		new_material['af_managed'] = True
		new_material['af_asset_id'] = asset_id

		return new_material

	def execute(self,context):
		af = bpy.context.window_manager.af
		implementation = af.current_implementation_list.implementations[af.current_implementation_list_index]
		asset_id = af.current_asset_list.assets[af.current_asset_list_index].name

		# Ensure that an empty temp directory is available
		temp_dir = os.path.join(tempfile.gettempdir(),"assetfetch-blender")
		if os.path.exists(temp_dir):
			os.rmdir(temp_dir)
		os.makedirs(temp_dir,exist_ok=True)
		
	
		for step in implementation.import_steps:

			if step.action == "directory_create":
				print(f"Creating directory {step.config['directory'].value}")
				os.makedirs(step.config['directory'].value,exist_ok=True)

			elif step.action == "unlock":

				pass
				
				

			
			elif step.action == "fetch_download":
				component : AF_PR_Component = implementation.get_component_by_id(step.config['component_id'].value)

				# Prepare query
				uri = component.file_fetch_download.uri
				method = component.file_fetch_download.method
				payload = component.file_fetch_download.payload
				query = http.AF_HttpQuery(uri=uri,method=method,parameters=payload)

				# Determine target path
				if component.file_info.behavior in ['file_passive','file_active']:
					# Download directly into local dir
					destination = os.path.join(implementation.local_directory,component.file_info.local_path)
				elif component.file_info.behavior == "archive":
					destination = os.path.join(temp_dir,component.name)
				else:
					raise Exception("Invalid behavior!")
				
				print(f"Downloading into {destination}")
				query.execute_as_file(destination_path=destination)

			elif step.action == "import_obj_from_local_path":
				# The path where the obj file was downloaded in a previous step
				obj_component = implementation.components[step.config['component_id'].value]
				obj_target_path = os.path.join(implementation.local_directory,obj_component.file_info.local_path)

				print(f"Importing OBJ from {obj_target_path}")

				up_axis = 'Y'
				use_mtl = True
				if "format_obj" in obj_component:
					if obj_component.format_obj.up_axis == "+y":
						up_axis = 'Y'
					elif obj_component.format_obj.up_axis == "+z":
						up_axis = 'Z'

					use_mtl = obj_component.format_obj.use_mtl

				bpy.ops.wm.obj_import(up_axis=up_axis,filepath=obj_target_path)
				imported_objects = bpy.context.selected_objects

				# remove materials from import (if requested)
				if not use_mtl:
					for obj in imported_objects:
						obj.active_material_index = 0
						for slot in obj.material_slots:
							with context.temp_override(object=obj):
								if slot.material:
									bpy.data.materials.remove(slot.material)
								bpy.ops.object.material_slot_remove()

						if "loose_material_apply" in obj_component:
							for material_declaration in obj_component.loose_material_apply:
								material_name = asset_id + "_" + material_name
								obj.data.materials.append(self.get_or_create_material(material_name,asset_id))
			else:
				raise Exception(f"No known procedure for action {step.action}")




		###########################################################################
		# Old code to be integrated into the new code above
		# Assuming that the implementations + index are set properly
		# Progress: https://stackoverflow.com/a/53877507

		#imported_components : Dict[str,any] = {}
		#downloaded_components: Dict[str,str] = {}
		"""
		impl = af_asset_implementations_options[af_asset_implementations_options_index]
		comps = json.loads(impl.components_json)

		asset_id = af_asset_list_entries.values()[af_asset_list_entries_index].name

		# Download
		for comp in comps:
			# obv. insecure without checks
			local_path = ASSETFETCH_HOME + f"{asset_id}/" + comp['data']['resolve_file']['local_path']
			if not os.path.isfile(local_path):
				os.makedirs(os.path.dirname(local_path), exist_ok=True)
				urllib.request.urlretrieve(comp['data']['resolve_file']['location'],local_path)
			else:	
				print(f"Skipping {local_path} because it already exists.")

		# Run Imports
		for comp in comps:
			local_path = ASSETFETCH_HOME + f"{asset_id}/" + comp['data']['resolve_file']['local_path']
			extension = comp['data']['resolve_file']['extension']

			if extension == ".obj":
				bpy.ops.wm.obj_import(up_axis='Y',filepath=local_path,)
				imported_objects = bpy.context.selected_objects

				# remove materials from import (if requested)
				for obj in imported_objects:
					obj.active_material_index = 0
					for slot in obj.material_slots:
						with context.temp_override(object=obj):
							if slot.material:
								bpy.data.materials.remove(slot.material)
							bpy.ops.object.material_slot_remove()

					if comp['data']['material_reference']['material_names']:
						for material_name in comp['data']['material_reference']['material_names']:
							material_name = asset_id + "_" + material_name
							obj.data.materials.append(self.get_or_create_material(material_name,asset_id))

			if extension == ".jpg":
				# Import the JPG file from local_path into blender
				image = bpy_extras.image_utils.load_image(local_path)

				if comp['data']['material_map']:
					material_name = asset_id + "_" + comp['data']['material_map']['material']
					material_map = asset_id + "_" + comp['data']['material_map']['map']
					
					
					target_material = self.get_or_create_material(material_name,asset_id)
					bsdf_shader = target_material.node_tree.nodes
					image_node = target_material.node_tree.nodes.new(type='ShaderNodeTexImage')
					image_node.image = image


					# Handle Color space

					# Connect
					target_material.node_tree.links.new(target_material.node_tree.nodes['TEX_COORD'].outputs['UV'],image_node.inputs['Vector'])
					if comp['data']['material_map']['map'] == "color":
						target_material.node_tree.links.new(image_node.outputs['Color'],target_material.node_tree.nodes['BSDF'].inputs['Base Color'])
					if comp['data']['material_map']['map'] == "normal":
						# Needs improved handling for multiple normal maps
						normal_map_node = target_material.node_tree.nodes.new(type="ShaderNodeNormalMap")
						target_material.node_tree.links.new(normal_map_node.outputs['Normal'],target_material.node_tree.nodes['BSDF'].inputs['Normal'])
						target_material.node_tree.links.new(image_node.outputs['Color'],normal_map_node.inputs['Color'])

		"""
		return {'FINISHED'}
	
registration_targets = [
	AF_OP_InitializeProvider,
	AF_OP_UpdateAssetList,
	AF_OP_UpdateImplementationsList,
	AF_OP_ExecuteImportPlan,
	AF_OP_ConnectionStatus
]