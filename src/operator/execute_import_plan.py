import logging
from typing import List
import zipfile
import bpy,bpy_extras,uuid,tempfile,os,shutil
import bpy_extras.image_utils
from ..util import http

LOGGER = logging.getLogger("af.execute_import_plan")
LOGGER.setLevel(logging.DEBUG)

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
	
	#AF_PR_LooseMaterialApplyBlock
	def assign_loose_materials(self,loose_material_apply_block,target_blender_objects:List[bpy.types.Object],af_namespace:str):
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
			LOGGER.error(f"Error while clearing local implementation directory: {e}")
		
		# Generate a namespace to use for loose materials
		# This tells the plugin whether an existing material is
		try:
			for step in implementation.import_steps:

				step_complete = False

				conf_log = {}
				for k in step.config.keys():
					conf_log[k] = step.config[k].value
				LOGGER.info(f"Running step {step.action} with config {conf_log}")

				# Create a new directory
				if step.action == "directory_create":
					os.makedirs(step.config['directory'].value,exist_ok=True)
					step_complete = True

				# Perform an unlocking query
				# This is the query that actually performs the purchase in the provider backend
				if step.action == "unlock":
					unlock_query  = implementation_list.get_unlock_query_by_id(step.config['query_id'].value)
					query : http.AF_HttpQuery = unlock_query.unlock_query.to_http_query()
					response = query.execute()
					unlock_query.unlocked = True
					
					step_complete = True
				

				# This code will fetch the file_fetch.download datablock that is missing on the locked asset.
				# It can do that now because the resource was already unlocked during a previous step.
				if step.action == "fetch_download_unlocked":
					component = implementation.get_component_by_id(step.config['component_id'].value)
					
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
					component = implementation.get_component_by_id(step.config['component_id'].value)

					# Prepare query
					query = component.file_fetch_download.to_http_query()

					# Determine target path
					if component.file_handle.behavior in ['single_active','single_passive']:
						# Download directly into local dir
						destination = os.path.join(implementation.local_directory,component.file_behavior.local_path)
					elif component.file_handle.behavior in ['archive_referenced_only','archive_unpack_fully']:
						destination = os.path.join(temp_dir,component.name)
					else:
						raise Exception("Invalid behavior!")
					
					query.execute_as_file(destination_path=destination)

					step_complete = True

				if step.action == "fetch_from_zip_archive":
					
					# Find the participating components
					file_component = implementation.get_component_by_id(step.config['component_id'].value)
					zip_component = implementation.get_component_by_id(file_component.file_fetch_from_archive.archive_component_id)

					# Build the relevant paths
	 				# Path to the source zip file. This is were the previous step has downloaded it to.
					source_zip_file_path = os.path.join(temp_dir,zip_component.name)

					# This is the path of the target file inside its parent zip
					source_zip_sub_path = file_component.file_fetch_from_archive.component_path

					# This is the final path where the file needs to end up
					destination_file_path = os.path.join(implementation.local_directory,file_component.file_behavior.local_path)
					
					with zipfile.ZipFile(source_zip_file_path, 'r') as zip_ref:
						# Check if the specified file exists in the zip archive
						if source_zip_sub_path not in zip_ref.namelist():
							raise Exception (f"File '{source_zip_sub_path}' not found in the zip archive.")
						
						# Prepare a temporary extraction dir
						extraction_id = str(uuid.uuid4())
						extraction_temp_dir = os.path.join(temp_dir,extraction_id)

						# Path were the file will initially land after extraction
						extraction_file_path = os.path.join(extraction_temp_dir,os.path.basename(source_zip_sub_path))
						
						# Actually run the extraction
						zip_ref.extract(source_zip_sub_path, extraction_temp_dir)

						# Move the file into the real destination path
						shutil.move(src=extraction_file_path,dst=destination_file_path)
						LOGGER.info(f"File '{source_zip_sub_path}' extracted successfully to '{destination_file_path}'.")

					step_complete = True

				
				if step.action == "import_usd_from_local_path":
					usd_component = implementation.get_component_by_id(step.config['component_id'].value)
					usd_target_path = os.path.join(implementation.local_directory,usd_component.file_handle.local_path)
					bpy.ops.wm.usd_import(filepath=usd_target_path,import_all_materials=True)

					step_complete = True

				if step.action == "import_obj_from_local_path":
					# The path where the obj file was downloaded in a previous step
					obj_component = implementation.get_component_by_id(step.config['component_id'].value)
					obj_target_path = os.path.join(implementation.local_directory,obj_component.file_handle.local_path)

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

					image_component  = implementation.get_component_by_id(step.config['component_id'].value)
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
		finally:
		
			# Refresh connection status
			if bpy.ops.af.connection_status.poll():
				bpy.ops.af.connection_status()

			# Rebuild import plans to accommodate any unlocked components
			bpy.ops.af.build_import_plans()

		return {'FINISHED'}