import glob
import hashlib
import json
import os
import shutil
import uuid
import bpy,math,tempfile
import bpy_extras.image_utils
import bpy.utils.previews
from typing import Dict,List

from src.property import AF_PR_AssetFetch, AF_PR_Component, AF_PR_Implementation, AF_PR_LooseMaterialApplyBlock, AF_PR_UnlockQuery
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

	# Clear thumbnail cache from memory to avoid leak
	if AF_OP_UpdateAssetList.thumbnail_icons:
		bpy.utils.previews.remove(AF_OP_UpdateAssetList.thumbnail_icons)

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
			af.current_provider_initialization.provider_configuration.connection_status_query.configure(provider_config['connection_status_query'])
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

		if af.current_provider_initialization.provider_configuration.connection_status_query.is_set:

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

	thumbnail_icons : bpy.utils.previews.ImagePreviewCollection = None

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):
		af : AF_PR_AssetFetch = bpy.context.window_manager.af

		# Ensure that an empty temp directory is available
		thumbnail_temp_dir = os.path.join(tempfile.gettempdir(),"assetfetch-blender-thumbs")
		if os.path.exists(thumbnail_temp_dir):
			shutil.rmtree(thumbnail_temp_dir)
		os.makedirs(thumbnail_temp_dir,exist_ok=True)

		# Contact asset list endpoint
		response = af.current_provider_initialization.asset_list_query.to_http_query().execute()
		
		# Save assets in blender properties
		af.current_asset_list.assets.clear()
		for asset in response.parsed['assets']:
			asset_entry = af.current_asset_list.assets.add()
			asset_entry.name = asset['id']

			# Text
			if "text" in asset['data']:
				asset_entry.text.configure(asset['data']['text'])
			
			# Implementations Query
			if "implementation_list_query" in asset['data']:
				asset_entry.implementation_list_query.configure(asset['data']['implementation_list_query'])

			if "preview_image_thumbnail" in asset['data']:
				asset_entry.preview_image_thumbnail.configure(asset['data']['preview_image_thumbnail'])

		af.current_asset_list_index = 0

		# Reset implementations list
		af.current_implementation_list.implementations.clear()

		# Find the best thumbnail resolution and download it
		target_resolution = 128
		thumbnail_library_reset = False
		for asset in af.current_asset_list.assets:
			
			if asset.preview_image_thumbnail.is_set:

				# Remove old thumbnails from memory
				if not thumbnail_library_reset:
					if AF_OP_UpdateAssetList.thumbnail_icons:
						bpy.utils.previews.remove(AF_OP_UpdateAssetList.thumbnail_icons)
					AF_OP_UpdateAssetList.thumbnail_icons = bpy.utils.previews.new()
					thumbnail_library_reset = True

				# Start using the string index "0", if it is present
				# Otherwise use the first element in the uris array
				if "0" in asset.preview_image_thumbnail.uris:
					chosen_resolution = int(asset.preview_image_thumbnail.uris["0"].name)
				else:
					chosen_resolution = int(asset.preview_image_thumbnail.uris[0].name)
				current_best_deviation = abs(chosen_resolution-target_resolution)

				for thumb_res in asset.preview_image_thumbnail.uris.keys():
					thumb_res = int(thumb_res)
					if thumb_res > 0 and abs(chosen_resolution - thumb_res) < current_best_deviation:
						chosen_resolution = thumb_res
						current_best_deviation = abs(chosen_resolution-target_resolution)
				asset.preview_image_thumbnail.chosen_resolution = chosen_resolution

				# Perform the file download into temp directory
				asset.preview_image_thumbnail.temp_file_id = str(uuid.uuid4())
				thumb_file_location = os.path.join(thumbnail_temp_dir,asset.preview_image_thumbnail.temp_file_id)
				thumb_query = http.AF_HttpQuery(asset.preview_image_thumbnail.uris[str(asset.preview_image_thumbnail.chosen_resolution)],"get",None)
				thumb_query.execute_as_file(thumb_file_location)

				# Import the downloaded file
				AF_OP_UpdateAssetList.thumbnail_icons.load(
					name=asset.name,
					path=thumb_file_location,
					path_type='IMAGE'
				)
				asset.preview_image_thumbnail.icon_id = AF_OP_UpdateAssetList.thumbnail_icons[asset.name].icon_id

		return {'FINISHED'}

class AF_OP_BuildImportPlans(bpy.types.Operator):
	"""Populates every currently loaded implementation with a plan for how to import them, if possible."""
	
	bl_idname = "af.build_import_plans"
	bl_label = "Build Import Plans"
	bl_options = {"REGISTER"}

	def execute(self,context):
		af : AF_PR_AssetFetch = bpy.context.window_manager.af

		for current_impl in af.current_implementation_list.implementations:
			# Enter try-catch block
			# Failing this block causes an implementation to be considered unreadable.
			# If it passes, it is considered readable.
			
			try:
				
				# We start by assuming that the implementation is valid
				current_impl.is_valid = True

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
				already_scheduled_unlocking_query_ids = []
				for comp in current_impl.components:
					if comp.unlock_link.is_set:
						referenced_query : AF_PR_UnlockQuery = af.current_implementation_list.get_unlock_query_by_id(comp.unlock_link.unlock_query_id)
						if (not referenced_query.unlocked) and (referenced_query.name not in already_scheduled_unlocking_query_ids):
							current_impl.import_steps.add().set_action("unlock").set_config_value("query_id",comp.unlock_link.unlock_query_id)
							already_scheduled_unlocking_query_ids.append(comp.unlock_link.unlock_query_id)					

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
						raise Exception(f"{comp.name} is missing either a file_fetch.download, file_fetch.from_archive or unlock_link datablock.")

				for comp in current_impl.components:
					recursive_fetching_datablock_handler(comp)
					

				# Step 4: Plan how to import main model file
				# "Importing" includes loading the file using the software's native format handler
				# and creating or applying loose materials referenced in loose_material datablocks
				for comp in current_impl.components:
					if comp.file_info.behavior == "file_active":
						if comp.file_info.extension == ".obj":
							current_impl.import_steps.add().set_action("import_obj_from_local_path").set_config_value("component_id",comp.name)
						if comp.file_info.extension in [".usd",".usda",".usdc",".usdz"]:
							current_impl.import_steps.add().set_action("import_usd_from_local_path").set_config_value("component_id",comp.name)

				# Step 5: Plan how to import other files, such as loose materials
				for comp in current_impl.components:
					if comp.loose_material_define.is_set:
						current_impl.import_steps.add().set_action("import_loose_material_map_from_local_path").set_config_value("component_id",comp.name)


			except Exception as e:
				current_impl.is_valid = False
				current_impl.validation_messages.add().set("crit",str(e))
				raise e
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

		# Load the data into the implementation_list
		af.current_implementation_list.configure(response.parsed)

		# Update import plans
		bpy.ops.af.build_import_plans()

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
		implementation_list = af.current_implementation_list
		return len(implementation_list.implementations) > 0 and implementation_list.implementations[af.current_implementation_list_index].is_valid
	
	
	def get_or_create_material(self,material_name:str,af_namespace:str):
		
		for existing_material in bpy.data.materials:
			if ("af_name" in existing_material) and ("af_namespace" in existing_material):
				if existing_material['af_name'] == material_name and existing_material['af_namespace'] == af_namespace:
					return existing_material

		new_material= bpy.data.materials.new(name=material_name)
		new_material.use_nodes = True

		# Add principled bsdf and tex coord
		new_material.node_tree.nodes.clear()
		output = new_material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
		output.name = "OUTPUT"
		bsdf_shader = new_material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
		bsdf_shader.name = "BSDF"
		tex_coord = new_material.node_tree.nodes.new(type='ShaderNodeTexCoord')
		tex_coord.name = "TEX_COORD"

		# Basic links
		new_material.node_tree.links.new(bsdf_shader.outputs['BSDF'],output.inputs['Surface'])

		# Mark as AssetFetch-managed
		new_material['af_namespace'] = af_namespace
		new_material['af_name'] = material_name

		return new_material	
	
	def assign_loose_materials(self,loose_material_apply_block:AF_PR_LooseMaterialApplyBlock,target_blender_objects:List[bpy.types.Object],af_namespace:str):
		if loose_material_apply_block.is_set:
			for obj in target_blender_objects:
				obj.data.materials.clear()
				for material_declaration in loose_material_apply_block.items:
					target_material = self.get_or_create_material(material_name=material_declaration.material_name,af_namespace=af_namespace)
					obj.data.materials.append(target_material)

	def execute(self,context):

		# Prepare helpful variables
		af = bpy.context.window_manager.af
		implementation_list = af.current_implementation_list
		implementation = implementation_list.implementations[af.current_implementation_list_index]
		asset_id = af.current_asset_list.assets[af.current_asset_list_index].name

		# Namespace for this import execution (used for loose material linking)
		af_namespace = str(uuid.uuid4())

		# Ensure that an empty temp directory is available
		temp_dir = os.path.join(tempfile.gettempdir(),"assetfetch-blender-temp-dl")
		if os.path.exists(temp_dir):
			shutil.rmtree(temp_dir)
		os.makedirs(temp_dir,exist_ok=True)

		# Clear the local implementation_directory
		try:
			if os.path.exists(implementation.local_directory):
				shutil.rmtree(implementation.local_directory)
			os.makedirs(implementation.local_directory,exist_ok=True)
		except Exception as e:
			print(e)
		
		# Generate a namespace to use for loose materials
		# This tells the plugin whether an existing material is

		for step in implementation.import_steps:

			step_complete = False

			if step.action == "directory_create":
				print(f"Creating directory {step.config['directory'].value}")
				os.makedirs(step.config['directory'].value,exist_ok=True)
				step_complete = True

			if step.action == "unlock":
				unlock_query : AF_PR_UnlockQuery = implementation_list.get_unlock_query_by_id(step.config['query_id'].value)
				query : http.AF_HttpQuery = unlock_query.unlock_query.to_http_query()
				response = query.execute()
				if response.is_ok:
					unlock_query.unlocked = True
				else:
					raise Exception(f"Unlocking Query {unlock_query.name} failed.")
				
				step_complete = True
			

			# This code will fetch the file_fetch.download datablock that is missing on the locked asset.
			# It can do that now because the resource was already unlocked during a previous step.
			if step.action == "fetch_download_unlocked":
				component : AF_PR_Component = implementation.get_component_by_id(step.config['component_id'].value)
				
				# Perform the query to get the previously withheld datablocks
				response = component.unlock_link.unlocked_datablocks_query.to_http_query().execute()
				
				# Add the real download configuration to the component so that it can be called in the next step.
				if "file_fetch.download" in response.parsed['data']:
					component.file_fetch_download.configure(response.parsed['data']['file_fetch.download'])
				else:
					raise Exception(f"Could not get unlocked download link for component {component.name}")

			# Actually download the asset file.
			# The data was either there already or has been fetched using the code above (action=file_download_unlocked)
			# In both cases, this code below actually downloads the asset and places it in its desired place
			if step.action in ["fetch_download","fetch_download_unlocked"]:
				component : AF_PR_Component = implementation.get_component_by_id(step.config['component_id'].value)

				# Prepare query
				query = component.file_fetch_download.to_http_query()

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

				step_complete = True
			
			if step.action == "import_usd_from_local_path":
				usd_component = implementation.get_component_by_id(step.config['component_id'].value)
				usd_target_path = os.path.join(implementation.local_directory,usd_component.file_info.local_path)
				print(f"Importing USD from {usd_target_path}")
				bpy.ops.wm.usd_import(filepath=usd_target_path,import_all_materials=True)

				step_complete = True

			if step.action == "import_obj_from_local_path":
				# The path where the obj file was downloaded in a previous step
				obj_component = implementation.get_component_by_id(step.config['component_id'].value)
				obj_target_path = os.path.join(implementation.local_directory,obj_component.file_info.local_path)

				print(f"Importing OBJ from {obj_target_path}")

				up_axis = 'Y'
				if "format_obj" in obj_component:
					if obj_component.format_obj.up_axis == "+y":
						up_axis = 'Y'
					elif obj_component.format_obj.up_axis == "+z":
						up_axis = 'Z'

				bpy.ops.wm.obj_import(up_axis=up_axis,filepath=obj_target_path)

				# Apply materials, if referenced
				self.assign_loose_materials(
					loose_material_apply_block=obj_component.loose_material_apply,
					target_blender_objects=bpy.context.selected_objects,
					af_namespace=af_namespace)
				
				step_complete = True
			
			if step.action == "import_loose_material_map_from_local_path":

				image_component : AF_PR_Component = implementation.get_component_by_id(step.config['component_id'].value)
				image_target_path = os.path.join(implementation.local_directory,image_component.file_info.local_path)
				target_material = self.get_or_create_material(material_name=image_component.loose_material_define.material_name,af_namespace=af_namespace)

				# Import the file from local_path into blender
				image = bpy_extras.image_utils.load_image(imagepath=image_target_path)

				# Set color space
				if image_component.loose_material_define.colorspace == "linear":
					image.colorspace_settings.name = "Non-Color"
				else:
					image.colorspace_settings.name = "sRGB"

				# Assign the map to the material
				#bsdf_shader = target_material.node_tree.nodes
				image_node = target_material.node_tree.nodes.new(type='ShaderNodeTexImage')
				image_node.image = image

				# Connect
				target_material.node_tree.links.new(target_material.node_tree.nodes['TEX_COORD'].outputs['UV'],image_node.inputs['Vector'])
				
				# Make connection into bsdf shader
				map = image_component.loose_material_define.map
				image_color_out = image_node.outputs['Color']
				bsdf_inputs = target_material.node_tree.nodes['BSDF'].inputs

				# Color Map
				if map in ['albedo','diffuse']:
					color_image_node = target_material.node_tree.links.new(image_color_out,bsdf_inputs['Base Color'])

				# Normal Map
				if map in ['normal+y','normal-y']:
					normal_map_node = target_material.node_tree.nodes.new(type="ShaderNodeNormalMap")
					target_material.node_tree.links.new(normal_map_node.outputs['Normal'],target_material.node_tree.nodes['BSDF'].inputs['Normal'])
					if map == "normal+y":
						target_material.node_tree.links.new(image_node.outputs['Color'],normal_map_node.inputs['Color'])
					if map == "normal-y":
						# Green channel must be inverted
						# Separate Color
						separate_color_node = target_material.node_tree.nodes.new(type="ShaderNodeSeparateColor")
						target_material.node_tree.links.new(image_node.outputs['Color'],separate_color_node.inputs['Color'])
						# Invert Green
						invert_normal_y_node = target_material.node_tree.nodes.new(type="ShaderNodeInvert")
						target_material.node_tree.links.new(separate_color_node.outputs['Green'],invert_normal_y_node.inputs['Color'])
						# Combine again
						combine_color_node = target_material.node_tree.nodes.new(type="ShaderNodeCombineColor")
						target_material.node_tree.links.new(invert_normal_y_node.outputs['Color'],combine_color_node.inputs['Green'])
						target_material.node_tree.links.new(separate_color_node.outputs['Red'],combine_color_node.inputs['Red'])
						target_material.node_tree.links.new(separate_color_node.outputs['Blue'],combine_color_node.inputs['Blue'])
						# Connect to normal node
						target_material.node_tree.links.new(combine_color_node.outputs['Color'],normal_map_node.inputs['Color'])

				# Roughness Map
				if map == "roughness":
					target_material.node_tree.links.new(image_color_out,bsdf_inputs['Roughness'])

				# Glossiness
				if map == "glossiness":
					# Map needs to be inverted
					invert_roughness_node = target_material.node_tree.nodes.new(type="ShaderNodeInvert")
					target_material.node_tree.links.new(image_color_out,invert_roughness_node.inputs['Color'])
					target_material.node_tree.links.new(invert_roughness_node.outputs['Color'],bsdf_inputs['Roughness'])

				# Metalness Map
				if map == "metallic":
					target_material.node_tree.links.new(image_color_out,bsdf_inputs['Metallic'])

				# Height
				if map == "height":
					displacement_node = target_material.node_tree.nodes.new("ShaderNodeDisplacement")
					target_material.node_tree.links.new(image_color_out,displacement_node.inputs['Height'])
					target_material.node_tree.links.new(displacement_node.outputs['Displacement'],target_material.node_tree.nodes['OUTPUT'].inputs['Displacement'])
				
				# Opacity
				if map == "opacity":
					target_material.node_tree.links.new(image_color_out,bsdf_inputs['Alpha'])

				if map == "emission":
					target_material.node_tree.links.new(image_color_out,bsdf_inputs['Emission Color'])

				step_complete = True

			if not step_complete:
				raise Exception(f"Step {step.action} could not be completed.")

		###########################################################################

		# Progress: https://stackoverflow.com/a/53877507
		
		# Refresh connection status
		bpy.ops.af.connection_status()

		return {'FINISHED'}
	
registration_targets = [
	AF_OP_InitializeProvider,
	AF_OP_UpdateAssetList,
	AF_OP_UpdateImplementationsList,
	AF_OP_BuildImportPlans,
	AF_OP_ExecuteImportPlan,
	AF_OP_ConnectionStatus
]