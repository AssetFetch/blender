import logging
import random
from typing import Dict, List, Set
import zipfile
from bpy.types import Context, Event
import bpy, bpy_extras, uuid, tempfile, os, shutil
import bpy_extras.image_utils

from ..property.core import *
from ..util.addon_constants import *
from ..util import http, material, af_constants, world

# Prepare logging
LOGGER = logging.getLogger("af.execute_import_plan")
LOGGER.setLevel(logging.DEBUG)


class AF_OP_ExecuteImportPlan(bpy.types.Operator):
	"""Executes the currently selected import plan which was constructured by the build_import_plans operator.
	Every type of step in the import plan has a dedicated function in this method
	which runs the action associated with it using the configuration data stored for the step."""

	bl_idname = "af.execute_import_plan"
	bl_label = "Execute Import Plan"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	def __init__(self):

		# Initialize variables
		self.af: AF_PR_AssetFetch = bpy.context.window_manager.af
		self.implementation_list: AF_PR_ImplementationList = self.af.current_implementation_list
		self.implementation: AF_PR_Implementation = self.implementation_list.implementations[self.af.current_implementation_list_index]
		self.asset_id: str = self.af.current_asset_list.assets[self.af.current_asset_list_index].name

		# Namespace for this import execution (used for loose material linking)
		# This will later be used to tell materials apart in the case of naming conflicts.
		self.af_namespace: str = str(uuid.uuid4())

		# Calculate the path for the temp directory
		self.temp_dir: str = os.path.join(tempfile.gettempdir(), "assetfetch-blender-temp-dl")

		# Variable to keep track of ongoing downloads
		self.ongoing_queries = {}

		# Lookup for functions to use
		# This object associates every import action type to its dedicated function
		self.step_functions = {
			AF_ImportAction.fetch_download.value: self.step_fetch_download,
			AF_ImportAction.fetch_from_zip_archive.value: self.step_fetch_from_zip_archive,
			AF_ImportAction.import_obj_from_local_path.value: self.step_import_obj_from_local_path,
			AF_ImportAction.import_usd_from_local_path.value: self.step_import_usd_from_local_path,
			AF_ImportAction.import_loose_material_map_from_local_path.value: self.step_import_loose_material_map_from_local_path,
			AF_ImportAction.import_loose_environment_from_local_path.value: self.step_import_loose_environment_from_local_path,
			AF_ImportAction.unlock.value: self.step_unlock,
			AF_ImportAction.create_directory.value: self.step_create_directory
		}

	# HELPER FUNCTIONS

	def helper_assign_loose_materials(self, loose_material_apply_block, target_blender_objects: List[bpy.types.Object], af_namespace: str):
		"""Takes in a loose_material.apply datablock and a list of Blender objects and applies the materials as defined."""
		if loose_material_apply_block.is_set:
			for obj in target_blender_objects:
				obj.data.materials.clear()
				for material_declaration in loose_material_apply_block.items:
					target_material = material.get_or_create_material(material_name=material_declaration.material_name, af_namespace=af_namespace)
					obj.data.materials.append(target_material)

	# STEP FUNCTIONS

	def step_unlock(self, query_id: str) -> AF_ImportActionState:
		"""Perform an unlock query."""
		unlock_query = self.implementation_list.get_unlock_query_by_id(query_id)
		query: http.AF_HttpQuery = unlock_query.unlock_query.to_http_query()
		response = query.execute(raise_for_status=True)
		unlock_query.unlocked = True
		return AF_ImportActionState.completed

	def step_create_directory(self, directory: str) -> AF_ImportActionState:
		"""Create a new directory"""
		os.makedirs(directory, exist_ok=True)
		return AF_ImportActionState.completed

	def step_fetch_download(self, component_id: str, max_runtime: float = 2.0) -> AF_ImportActionState:
		""" Download the asset file.
		This code below downloads the asset and places it in its desired location
		The operator can't run continuously for a long period, it has to "check in" with Blender to prevent the
		application from timing out. Therefore the download is performed in chunks which is reflected in the
		two scenarios outlined in the code. """

		component = self.implementation.get_component_by_id(component_id)

		# Scenario 1: The download is ongoing and may or may not finish during this iteration
		if (component_id in self.ongoing_queries):
			current_query = self.ongoing_queries[component_id]
			ongoing = current_query.execute_as_file_piecewise_next_chunk()
			if ongoing:
				self.implementation.get_current_step().completion = current_query.get_download_completeness()
				return AF_ImportActionState.running
			else:
				current_query.execute_as_file_piecewise_finish()
				return AF_ImportActionState.completed

		# Scenario 2: The download hasn't been started yet and must be started
		else:
			# Prepare query
			query: AF_HttpQuery = component.fetch_download.download_query.to_http_query()

			# Determine target path
			destination = os.path.join(self.implementation.local_directory, component.store.local_file_path)

			# Initialize the query
			query.execute_as_file_piecewise_start(destination_path=destination)

			# Register the query as an ongoing query
			self.ongoing_queries[component_id] = query
			return AF_ImportActionState.running

	def step_fetch_from_zip_archive(self, component_id: str) -> AF_ImportActionState:
		"""Fetches a component from the ZIP archive that it references in its file_fetch.from_archive datablock."""

		# Find the participating components
		file_component = self.implementation.get_component_by_id(component_id)
		zip_component = self.implementation.get_component_by_id(file_component.fetch_from_archive.archive_component_id)

		# Build the relevant paths
		# Path to the source zip file. This is were the previous step has downloaded it to.
		source_zip_file_path = os.path.join(self.implementation.local_directory,zip_component.store.local_file_path)

		# This is the path of the target file inside its parent zip
		source_zip_sub_path = file_component.fetch_from_archive.component_sub_path

		# This is the final path where the file needs to end up
		destination_file_path = os.path.join(self.implementation.local_directory, file_component.store.local_file_path)

		with zipfile.ZipFile(source_zip_file_path, 'r') as zip_ref:
			# Check if the specified file exists in the zip archive
			if source_zip_sub_path not in zip_ref.namelist():
				raise Exception(f"File '{source_zip_sub_path}' not found in the zip archive.")

			# Actually run the extraction
			with zip_ref.open(source_zip_sub_path) as source_file:
				# Write the content to the new location with a new name
				with open(destination_file_path, 'wb') as destination_file:
					shutil.copyfileobj(source_file,destination_file)

			LOGGER.info(f"File '{source_zip_sub_path}' extracted successfully to '{destination_file_path}'.")

		return AF_ImportActionState.completed

	def step_import_usd_from_local_path(self, component_id: str) -> AF_ImportActionState:
		"""Imports a USD file."""
		usd_component = self.implementation.get_component_by_id(component_id=component_id)
		usd_target_path = os.path.join(self.implementation.local_directory, usd_component.store.local_file_path)
		bpy.ops.wm.usd_import(filepath=usd_target_path, import_all_materials=True)

		return AF_ImportActionState.completed

	def step_import_obj_from_local_path(self, component_id: str) -> AF_ImportActionState:
		"""Imports an OBJ file."""
		# The path where the obj file was downloaded in a previous step
		obj_component = self.implementation.get_component_by_id(component_id=component_id)
		obj_target_path = os.path.join(self.implementation.local_directory, obj_component.store.local_file_path)

		up_axis = 'Y'
		if "format_obj" in obj_component:
			if obj_component.format_obj.up_axis == "+y":
				up_axis = 'Y'
			elif obj_component.format_obj.up_axis == "+z":
				up_axis = 'Z'

		bpy.ops.wm.obj_import(up_axis=up_axis, filepath=obj_target_path)

		# Apply materials, if referenced
		self.helper_assign_loose_materials(loose_material_apply_block=obj_component.loose_material_apply,
			target_blender_objects=bpy.context.selected_objects,
			af_namespace=self.af_namespace)

		return AF_ImportActionState.completed

	def step_import_loose_environment_from_local_path(self, component_id: str) -> AF_ImportActionState:
		"""Imports an HDRI environment from a file based on a loose_environment datablock"""

		hdri_component = self.implementation.get_component_by_id(component_id=component_id)
		hdri_target_path = os.path.join(self.implementation.local_directory, hdri_component.store.local_file_path)

		world.create_world(world_name=hdri_component.name, hdr_image_path=hdri_target_path, af_namespace=self.af_namespace)

		return AF_ImportActionState.completed

	def step_import_loose_material_map_from_local_path(self, component_id: str) -> AF_ImportActionState:
		"""Imports a material map and adds it to a material based on the loose_material.define datablock"""

		image_component = self.implementation.get_component_by_id(component_id=component_id)
		image_target_path = os.path.join(self.implementation.local_directory, image_component.store.local_file_path)
		target_material = material.get_or_create_material(material_name=image_component.handle_loose_material_map.material_name, af_namespace=self.af_namespace)

		map = af_constants.AF_MaterialMap.from_string_by_value(image_component.handle_loose_material_map.map)

		material.add_map_to_material(image_target_path=image_target_path, target_material=target_material, map=map)

		return AF_ImportActionState.completed

	# BLENDER FUNCTIONS

	@classmethod
	def poll(self, context):
		af = bpy.context.window_manager.af
		implementation_list = af.current_implementation_list

		if len(implementation_list.implementations) < 1:
			return False
		if not implementation_list.implementations[af.current_implementation_list_index].is_valid:
			return False
		if implementation_list.implementations[af.current_implementation_list_index].get_current_state() == AF_ImportActionState.running:
			return False
		return True

	def modal(self, context: Context, event: Event):

		# Schedule a GUI redrawing to run after this modal function
		for a in context.screen.areas:
			a.tag_redraw()

		# Find the next step that needs work
		current_step: AF_PR_ImplementationImportStep = self.implementation.get_current_step()

		if current_step is not None:

			# Cancel the ongoing import process if ESC is pressed
			if event.type in {'ESC'}:
				current_step.state = AF_ImportActionState.canceled.value
				print("USER_CANCEL")
				return {'CANCELLED'}

			# Cancel the ongoing import if the current step is already marked as canceled or failed
			# This mostly exists as a fallback because ideally the error would already be detected during execution and
			# then canceled immediately.
			if current_step.state in [AF_ImportActionState.failed.value, AF_ImportActionState.canceled.value]:
				print(f"AUTO_CANCEL because {current_step.state}")
				return {'CANCELLED'}

			# Actually run the function for the current step
			try:
				current_step.state = (self.step_functions[current_step.action](**current_step.get_config_as_function_parameters())).value
			except Exception as e:
				current_step.state = AF_ImportActionState.failed.value

				# Cancel ongoing queries in case of failure to avoid orphaned file locks.
				for q in self.ongoing_queries.values():
					q.execute_as_file_piecewise_finish()

				raise e

			# Raise exception if an unexpected state has been reached.
			if current_step.state not in [
				AF_ImportActionState.running.value, AF_ImportActionState.completed.value, AF_ImportActionState.failed.value, AF_ImportActionState.canceled.value
			]:
				raise Exception(f"Unexpected state during current step: {current_step.state}")

			return {'RUNNING_MODAL'}

		else:
			# Nothing left to do. Finish.
			if bpy.ops.af.connection_status.poll():
				bpy.ops.af.connection_status()
			return {'FINISHED'}

	def execute(self, context):

		# Clear the local implementation_directory
		try:
			if os.path.exists(self.implementation.local_directory):
				shutil.rmtree(self.implementation.local_directory)
			os.makedirs(self.implementation.local_directory, exist_ok=True)
		except Exception as e:
			LOGGER.error(f"Error while clearing local implementation directory: {e}")

		# Reset the state of the implementation
		self.implementation.reset_state()

		# Set up modal operation
		self._timer = context.window_manager.event_timer_add(0.125, window=context.window)
		context.window_manager.modal_handler_add(self)

		# Return and hand of the real work to the modal function
		return {'RUNNING_MODAL'}
