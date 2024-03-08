import hashlib
import json
import os
import bpy,math
import bpy_extras.image_utils
from typing import Dict,List
from . import http_handler
from . import implementations
import urllib

ASSETFETCH_HOME = os.path.expanduser('~')+"/AssetFetch/"

def sha1sum(filename):
    with open(filename, 'rb', buffering=0) as f:
        return hashlib.file_digest(f, 'sha1').hexdigest()

def register():
	bpy.utils.register_class(AF_OP_Initialize_Provider)
	bpy.utils.register_class(AF_OP_Update_Asset_List)
	bpy.utils.register_class(AF_OP_Update_Implementations_List)
	bpy.utils.register_class(AF_OP_Execute_Import_Plan)

def unregister():
	bpy.utils.unregister_class(AF_OP_Update_Asset_List)
	bpy.utils.unregister_class(AF_OP_Initialize_Provider)
	bpy.utils.unregister_class(AF_OP_Update_Implementations_List)
	bpy.utils.unregister_class(AF_OP_Execute_Import_Plan)

class AF_OP_Initialize_Provider(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.initialize_provider"
	bl_label = "Initialize Provider"
	bl_options = {"REGISTER","UNDO"}

	#url: StringProperty(name="URL")

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):

		# Contact initialization endpoint
		url = bpy.context.window_manager.af_initialize_provider_url
		query = http_handler.AF_HttpQuery(uri=url,method=http_handler.AF_HttpMethod.GET)
		response : http_handler.AF_HttpResponse = query.execute()

		#bpy.context.window_manager.af_initialize_provider_text = "OK"
		if "text" in response.parsed['data']:
			bpy.context.window_manager.af_initialize_provider_title = response.parsed['data']['text']['title']
		else:
			bpy.context.window_manager.af_initialize_provider_title = "Connected. (No title provided)."

		# Get the headers
		if "provider_configuration" in response.parsed['data']:
			bpy.context.window_manager.af_initialize_provider_headers.clear()
			for header_info in response.parsed['data']['headers']:
				current_header = bpy.context.window_manager.af_initialize_provider_headers.add()
				current_header.name = header_info['name']
				current_header.value = header_info['default']

		# Update the asset_list_url and related parameters
		if "asset_list_query" in response.parsed['data']:
			bpy.context.window_manager.af_asset_list_url = response.parsed['data']['asset_list_query']['uri']
			bpy.context.window_manager.af_asset_list_method = response.parsed['data']['asset_list_query']['method']
			bpy.context.window_manager.af_asset_list_parameters.clear()
			for parameter_info in response.parsed['data']['asset_list_query']['parameters']:
				current_parameter = bpy.context.window_manager.af_asset_list_parameters.add()
				current_parameter.name = parameter_info['name']
				current_parameter.type = parameter_info['type']
				if parameter_info['default']:
					current_parameter.value = parameter_info['default']
				else:
					current_parameter.value = ""
		else:
			raise Exception("No Asset List Query!")
		
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

		# Contact initialization endpoint
		url = bpy.context.window_manager.af_asset_list_url
		parameters : Dict[str,str] = {}
		for par in bpy.context.window_manager.af_asset_list_parameters:
			parameters[par.name] = par.value
		method = http_handler.AF_HttpMethod[bpy.context.window_manager.af_asset_list_method]

		query = http_handler.AF_HttpQuery(uri=url,method=method,parameters=parameters)
		response : http_handler.AF_HttpResponse = query.execute()
		
		# Liste leeren
		# neue Listenelemente für Assets einfügen
			# Implementations query
		
		bpy.context.window_manager.af_asset_list_entries.clear()
		for asset in response.parsed['assets']:
			asset_entry = bpy.context.window_manager.af_asset_list_entries.add()
			asset_entry.name = asset['id']
			asset_entry.text_title = asset['data']['text']['title']
			asset_entry.implementations_query_method = asset['implementations_query']['method']
			asset_entry.implementations_query_uri = asset['implementations_query']['uri']

			
			if asset['implementations_query']['parameters']:
				asset_entry.implementations_query_parameters.clear()
				for parameter_info in asset['implementations_query']['parameters']:
					current_parameter = asset_entry.implementations_query_parameters.add()
					current_parameter.name = parameter_info['name']
					current_parameter.type = parameter_info['type']
					if parameter_info['default']:
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
		url = bpy.context.window_manager.af_asset_list_entries.values()[bpy.context.window_manager.af_asset_list_entries_index].implementations_query_uri
		parameters : Dict[str,str] = {}
		for par in bpy.context.window_manager.af_asset_list_entries.values()[bpy.context.window_manager.af_asset_list_entries_index].implementations_query_parameters.values():
			parameters[par.name] = par.value
		method = http_handler.AF_HttpMethod[bpy.context.window_manager.af_asset_list_entries.values()[bpy.context.window_manager.af_asset_list_entries_index].implementations_query_method]

		query = http_handler.AF_HttpQuery(uri=url,method=method,parameters=parameters)
		raw_response : http_handler.AF_HttpResponse = query.execute()
		response = raw_response.parsed_json()
		
		# Find valid implementations
		bpy.context.window_manager.af_asset_implementations_options.clear()
		for impl in response:
			impl_validation = implementations.validate_implementation(impl)
			print(impl_validation)
			
			if impl_validation.ok:
				current_impl = bpy.context.window_manager.af_asset_implementations_options.add()
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

		impl = bpy.context.window_manager.af_asset_implementations_options[bpy.context.window_manager.af_asset_implementations_options_index]
		comps = json.loads(impl.components_json)

		asset_id = bpy.context.window_manager.af_asset_list_entries.values()[bpy.context.window_manager.af_asset_list_entries_index].name

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