import hashlib
import json
import os
import bpy,math
import bpy_extras.image_utils
from typing import Dict,List
from . import http
from . import implementations
import urllib

ASSETFETCH_HOME = os.path.expanduser('~')+"/AssetFetch/"

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

class AF_OP_Initialize_Provider(bpy.types.Operator):
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
		af = bpy.context.window_manager.af

		# Reset existing connection_state
		af['current_provider_initialization'].clear()
		af['current_connection_state'].clear()
		af['current_asset_list'].clear()
		af['current_asset_list_index'] = 0
		af['current_implementation_list'].clear()
		af['current_implementation_list_index'] = 0

		# Contact initialization endpoint and get the response
		query = http.AF_HttpQuery(uri=af.current_init_url,method="get")
		response : http.AF_HttpResponse = query.execute()

		# Get the provider text (title and description)
		if "text" in response.parsed['data']:
			dict_to_attr(response.parsed['data']['text'],['title','description'],af.current_provider_initialization.text)

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
			
			# Set URI and HTTP method
			dict_to_attr(response.parsed['data']['asset_list_query'],['uri','method'],af.current_provider_initialization.asset_list_query)

			# Set Parameters
			af.current_provider_initialization.asset_list_query.parameters.clear()
			for parameter_info in response.parsed['data']['asset_list_query']['parameters']:
				current_parameter = af.current_provider_initialization.asset_list_query.parameters.add()
				dict_to_attr(parameter_info,['type','name','title','default','mandatory','delimiter'],current_parameter)
				
				if "choices" in parameter_info:
					for choice in parameter_info['choices']:
						new_choice = current_parameter.choices.add()
						new_choice.value = choice
		else:
			raise Exception("No Asset List Query!")
		
		return {'FINISHED'}
	
class AF_OP_Connection_Status(bpy.types.Operator):
	"""Performs a status query to the provider, if applicable."""

	bl_idname = "af.connection_status"
	bl_label = "Get Connection Status"
	bl_options = {"REGISTER"}

	def execute(self,context):
		af = bpy.context.window_manager.af

		# Contact initialization endpoint and get the response
		query = http.AF_HttpQuery(uri=af.current_provider_initialization.provider_configuration.connection_status_query.uri,method=af.current_provider_initialization.provider_configuration.connection_status_query.method)
		response : http.AF_HttpResponse = query.execute()

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



class AF_OP_Update_Asset_List(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.update_asset_list"
	bl_label = "Update Asset List"
	bl_options = {"REGISTER","UNDO"}

	#url: StringProperty(name="URL")

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):
		af = bpy.context.window_manager.af

		# Contact initialization endpoint
		parameters : Dict[str,str] = {}
		for par in af.current_provider_initialization.asset_list_query.parameters:
			parameters[par.name] = par.value
		query = http.AF_HttpQuery(
			uri=af.current_provider_initialization.asset_list_query.uri,
			method=af.current_provider_initialization.asset_list_query.method,
			parameters=parameters)
		response : http.AF_HttpResponse = query.execute()
		
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
			asset_entry.implementation_list_query.parameters.clear()
			if "implementation_list_query" in asset['data']:
				dict_to_attr(asset['data']['implementation_list_query'],['uri','method'],asset_entry.implementation_list_query)

				for parameter_info in asset['data']['implementation_list_query']['parameters']:
					current_parameter = asset_entry.implementation_list_query.parameters.add()
					current_parameter.name = parameter_info['name']
					current_parameter.type = parameter_info['type']
					if "default" in parameter_info:
						current_parameter.value = parameter_info['default']
					else:
						current_parameter.value = ""
		
		return {'FINISHED'}

class AF_OP_Update_Implementations_List(bpy.types.Operator):
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

		# Contact implementations endpoint
		url = af_asset_list_entries.values()[af_asset_list_entries_index].implementations_query_uri
		parameters : Dict[str,str] = {}
		for par in af_asset_list_entries.values()[af_asset_list_entries_index].implementations_query_parameters.values():
			parameters[par.name] = par.value
		method = http.AF_HttpMethod[af_asset_list_entries.values()[af_asset_list_entries_index].implementations_query_method]

		query = http.AF_HttpQuery(uri=url,method=method,parameters=parameters)
		raw_response : http.AF_HttpResponse = query.execute()
		response = raw_response.parsed_json()
		
		# Find valid implementations
		af_asset_implementations_options.clear()
		for impl in response:
			impl_validation = implementations.validate_implementation(impl)
			print(impl_validation)
			
			if impl_validation.ok:
				current_impl = af_asset_implementations_options.add()
				current_impl.name = impl['id']
				current_impl.components_json = json.dumps(impl['components'])

			
		return {'FINISHED'}
	
class AF_OP_Execute_Import_Plan(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.execute_import_plan"
	bl_label = "Execute Import Plan"
	bl_options = {"REGISTER","UNDO"}

	#url: StringProperty(name="URL")

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')
	
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

		# Assuming that the implementations + index are set properly
		# Progress: https://stackoverflow.com/a/53877507

		#imported_components : Dict[str,any] = {}
		#downloaded_components: Dict[str,str] = {}

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


		return {'FINISHED'}
	
registration_targets = [
	AF_OP_Initialize_Provider,
	AF_OP_Update_Asset_List,
	AF_OP_Update_Implementations_List,
	AF_OP_Execute_Import_Plan,
	AF_OP_Connection_Status
]