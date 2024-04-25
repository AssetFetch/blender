import logging
import random
from typing import Dict, List, Set
import zipfile
from bpy.types import Context, Event
import bpy,bpy_extras,uuid,tempfile,os,shutil
import bpy_extras.image_utils

from ..property.core import *
from ..util import http,material,af_constants

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
	
	#AF_PR_LooseMaterialApplyBlock
	def assign_loose_materials(self,loose_material_apply_block,target_blender_objects:List[bpy.types.Object],af_namespace:str):
		if loose_material_apply_block.is_set:
			for obj in target_blender_objects:
				obj.data.materials.clear()
				for material_declaration in loose_material_apply_block.items:
					target_material = material.get_or_create_material(material_name=material_declaration.material_name,af_namespace=af_namespace)
					obj.data.materials.append(target_material)

	def __init__(self):
		print("INIT")

		# INITIALIZE VARIABLES
  
		self.af : AF_PR_AssetFetch = bpy.context.window_manager.af
		self.implementation_list : AF_PR_ImplementationList = self.af.current_implementation_list
		self.implementation : AF_PR_Implementation = self.implementation_list.implementations[self.af.current_implementation_list_index]
		self.asset_id : str = self.af.current_asset_list.assets[self.af.current_asset_list_index].name

		# Namespace for this import execution (used for loose material linking)
		self.af_namespace : str = str(uuid.uuid4())

		# Ensure that temp directory exists
		self.temp_dir : str = os.path.join(tempfile.gettempdir(),"assetfetch-blender-temp-dl")

		# Variable to keep track of ongoing downloads
		self.ongoing_downloads = Dict[str,AF_HttpQuery]

	def modal(self, context: Context, event: Event):
		print("MODAL")

		

		# Schedule a GUI redrawing to run after this modal
		for a in context.screen.areas:
			a.tag_redraw()

		# Find the next step that needs work
		current_step : AF_PR_ImplementationImportStep = self.implementation.get_current_step()

		if current_step is not None:
			
			# Cancel the ongoing import process if ESC is pressed
			if event.type in {'ESC'}: 
				current_step.state = addon_constants.AF_ImportActionState.canceled.value
				print("USER_CANCEL")
				return {'CANCELLED'}
			
			# Cancel the ongoing import if the current step is already marked as canceled or failed
			# This mostly exists as a fallback because ideally the error would already be detected during execution and
			# then canceled immediately.
			if current_step.state in [addon_constants.AF_ImportActionState.failed.value,addon_constants.AF_ImportActionState.canceled.value]:
				print("AUTO_CANCEL")
				return {'CANCELED'}
			
			# directory_create - Create a new directory
			if current_step.action == addon_constants.AF_ImportAction.directory_create.value:
				os.makedirs(current_step.config['directory'].value,exist_ok=True)
				current_step.state = addon_constants.AF_ImportActionState.completed.value
				return {'RUNNING_MODAL'}
			

			


		else:
			return {'FINISHED'}


		context.window_manager.af.current_import_execution_progress = random.uniform(0,1)
		
		
		
		if context.window_manager.af.current_import_execution_progress  > 0.95:
			print("FINISHED")
			return {'FINISHED'}

		return {'PASS_THROUGH'}

	def execute(self,context):
		print("EXECUTE")

		# Ensure that an empty temp directory is available
		if os.path.exists(self.temp_dir):
			shutil.rmtree(self.temp_dir)
		os.makedirs(self.temp_dir,exist_ok=True)

		# Clear the local implementation_directory
		try:
			if os.path.exists(self.implementation.local_directory):
				shutil.rmtree(self.implementation.local_directory)
			os.makedirs(self.implementation.local_directory,exist_ok=True)
		except Exception as e:
			LOGGER.error(f"Error while clearing local implementation directory: {e}")

		# Set up modal operation
		self._timer = context.window_manager.event_timer_add(1, window=context.window)
		context.window_manager.modal_handler_add(self)

		# Return and hand of the real work to the modal function
		return {'RUNNING_MODAL'}


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
						destination = os.path.join(implementation.local_directory,component.file_handle.local_path)
					elif component.file_handle.behavior in ['archive_unpack_referenced','archive_unpack_fully']:
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
					destination_file_path = os.path.join(implementation.local_directory,file_component.file_handle.local_path)
					
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
					image_target_path = os.path.join(implementation.local_directory,image_component.file_handle.local_path)
					target_material = material.get_or_create_material(material_name=image_component.loose_material_define.material_name,af_namespace=af_namespace)

					colorspace = af_constants.AF_Colorspace[image_component.loose_material_define.colorspace]
					map = af_constants.AF_MaterialMap.from_string_by_value(image_component.loose_material_define.map)

					material.add_map_to_material(
						colorspace=colorspace,
						image_target_path=image_target_path,
						target_material=target_material,
						map=map)
					
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