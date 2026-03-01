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


class AF_OT_ExecuteImportPlan(bpy.types.Operator):
	"""Executes the currently selected import plan which was constructured by the build_import_plans operator.
	Every type of step in the import plan has a dedicated function in this method
	which runs the action associated with it using the configuration data stored for the step."""

	bl_idname = "af.execute_import_plan"
	bl_label = "Execute Import Plan"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	# HELPER FUNCTIONS

	def helper_assign_loose_materials(self, link_loose_material_block, target_blender_objects: List[bpy.types.Object], af_namespace: str):
		"""Takes in a link.loose_material datablock and a list of Blender objects and applies the materials as defined.
		This function is used when importing geometry files like obj/fbx/..."""
		if link_loose_material_block.is_set:
			for obj in target_blender_objects:
				obj.data.materials.clear()
				target_material = material.get_or_create_material(material_name=link_loose_material_block.material_name, af_namespace=af_namespace)
				obj.data.materials.append(target_material)

	def clear_implementation_directory(self, implementation: AF_PR_Implementation):
		"""Empties the local implementation directory on disk to prepare for a fresh import.
		This is used at the start of the import process to ensure that there are no leftover files from previous imports."""

		try:
			if os.path.exists(implementation.local_directory):
				shutil.rmtree(implementation.local_directory)
			os.makedirs(implementation.local_directory, exist_ok=True)
		except Exception as e:
			LOGGER.error(f"Error while clearing local implementation directory: {e}")

	# STEP FUNCTIONS

	def step_unlock(self, query_id: str) -> AF_ImportActionState:
		"""Perform an unlock query."""
		unlock_query = self.implementation_list.get_unlock_query_by_id(query_id)
		query: http.AF_HttpQuery = unlock_query.query.to_http_query()
		response = query.execute(raise_for_status=True)
		unlock_query.unlocked = True
		return AF_ImportActionState.completed

	def step_create_directory(self, directory: str) -> AF_ImportActionState:
		"""Create a new directory"""
		os.makedirs(directory, exist_ok=True)
		return AF_ImportActionState.completed

	def step_fetch_download(self, component_id: str) -> AF_ImportActionState:
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
				del self.ongoing_queries[component_id]
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

			# Set initial progress
			self.implementation.get_current_step().completion = 0.0

			return AF_ImportActionState.running

	def step_fetch_from_zip_archive(self, component_id: str) -> AF_ImportActionState:
		"""Fetches a component from the ZIP archive that it references in its file_fetch.from_archive datablock."""

		# Find the participating components
		file_component = self.implementation.get_component_by_id(component_id)
		zip_component = self.implementation.get_component_by_id(file_component.fetch_from_archive.archive_component_id)

		# Build the relevant paths
		# Path to the source zip file. This is were the previous step has downloaded it to.
		source_zip_file_path = os.path.join(self.implementation.local_directory, zip_component.store.local_file_path)

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
					shutil.copyfileobj(source_file, destination_file)

			LOGGER.info(f"File '{source_zip_sub_path}' extracted successfully to '{destination_file_path}'.")

		return AF_ImportActionState.completed

	def step_extract_zip_archive_fully(self, component_id: str) -> AF_ImportActionState:
		"""Extracts the entire contents of a ZIP archive into the target directory
		specified by the handle_archive datablock's local_directory_path."""

		archive_component = self.implementation.get_component_by_id(component_id)
		source_zip_file_path = os.path.join(self.implementation.local_directory, archive_component.store.local_file_path)

		# Determine the extraction target directory
		local_dir_path = archive_component.handle_archive.local_directory_path
		if local_dir_path and local_dir_path != '/':
			# Strip leading slashes to prevent os.path.join from treating it as an absolute path
			extract_dir = os.path.join(self.implementation.local_directory, local_dir_path.lstrip('/'))
		else:
			extract_dir = self.implementation.local_directory

		os.makedirs(extract_dir, exist_ok=True)

		with zipfile.ZipFile(source_zip_file_path, 'r') as zip_ref:
			zip_ref.extractall(extract_dir)

		LOGGER.info(f"Archive '{source_zip_file_path}' fully extracted to '{extract_dir}'.")

		return AF_ImportActionState.completed

	def step_delete_archive(self, component_id: str) -> AF_ImportActionState:
		"""Deletes the ZIP archive file specified by the component_id from the local implementation directory.
		This is used to clean up ZIP files after their contents have been extracted."""

		archive_component = self.implementation.get_component_by_id(component_id)
		archive_file_path = os.path.join(self.implementation.local_directory, archive_component.store.local_file_path)

		if os.path.exists(archive_file_path):
			os.remove(archive_file_path)
			LOGGER.info(f"Deleted archive file at '{archive_file_path}'.")
		else:
			LOGGER.warning(f"Attempted to delete archive file at '{archive_file_path}', but it does not exist.")

		return AF_ImportActionState.completed

	def step_import_usd_from_local_path(self, component_id: str) -> AF_ImportActionState:
		"""Imports a USD file."""
		usd_component = self.implementation.get_component_by_id(component_id=component_id)
		usd_target_path = os.path.join(self.implementation.local_directory, usd_component.store.local_file_path)
		bpy.ops.wm.usd_import(filepath=usd_target_path, import_all_materials=True)

		return AF_ImportActionState.completed

	def step_import_local_implementation_dir_to_blender_asset_library(self, component_id: str) -> AF_ImportActionState:
		"""Imports the entire contents of the implementation directory into a subfolder in Blender's Asset Library.
		The subfolder is named after the asset and provider to ensure that there are no naming conflicts between different assets."""

		prefs = AF_PR_Preferences.get_prefs()
		target_library_name = prefs.blend_target_asset_library

		# Shorthands for building the destination path
		af = bpy.context.window_manager.af
		provider_id = af.current_provider_initialization.name
		asset_id = af.current_asset_list.assets[af.current_asset_list_index].name
		implementation_id = af.current_implementation_list.implementations[af.current_implementation_list_index].name

		if target_library_name and target_library_name != "NONE":
			for lib in bpy.context.preferences.filepaths.asset_libraries:
				if lib.name == target_library_name:

					# Build the path inside the asset library
					dest_path = os.path.join(lib.path, provider_id, asset_id, implementation_id)
					os.makedirs(dest_path, exist_ok=True)

					# Copy over the files
					shutil.copytree(self.implementation.local_directory, dest_path, dirs_exist_ok=True)
					LOGGER.info(f"Copied asset .blend file to library '{lib.name}' at '{dest_path}'")

					# Clear the implementation directory.
					# The files have been moved to their new place in the asset library.
					# We skip this, if the implementation dir is already in the asset lib.
					if not self.implementation.local_directory.startswith(lib.path):
						self.clear_implementation_directory(self.implementation)
					break

		return AF_ImportActionState.completed

	def step_import_blend_from_local_path(self, component_id: str) -> AF_ImportActionState:
		"""Imports data from a .blend file. If the format.blend datablock specifies targets,
		only those specific data-blocks are imported. Otherwise all objects are appended.
		If the file is marked as an asset and a target asset library is configured,
		the .blend file is also copied into that library's directory."""

		blend_component = self.implementation.get_component_by_id(component_id=component_id)
		blend_target_path = os.path.join(self.implementation.local_directory, blend_component.store.local_file_path)

		has_targets = blend_component.format_blend.is_set and len(blend_component.format_blend.targets) > 0

		if has_targets:
			# Selectively import only the specified targets
			with bpy.data.libraries.load(blend_target_path, link=False) as (data_from, data_to):  # pyright: ignore[reportGeneralIssues]
				for target in blend_component.format_blend.targets:
					kind = target.kind
					names_to_import = [n.value for n in target.names]
					available = getattr(data_from, kind, [])
					filtered = [n for n in names_to_import if n in available]
					if filtered:
						setattr(data_to, kind, filtered)

			# Link imported objects and collections into the scene
			if hasattr(data_to, 'objects'):
				for obj in data_to.objects:
					if obj is not None:
						bpy.context.collection.objects.link(obj)
			if hasattr(data_to, 'collections'):
				for coll in data_to.collections:
					if coll is not None:
						bpy.context.scene.collection.children.link(coll)
		else:
			# No targets: append all objects
			with bpy.data.libraries.load(blend_target_path, link=False) as (data_from, data_to):  # pyright: ignore[reportGeneralIssues]
				data_to.objects = data_from.objects

			for obj in data_to.objects:
				if obj is not None:
					bpy.context.collection.objects.link(obj)

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

		# Apply loose materials, if referenced
		self.helper_assign_loose_materials(link_loose_material_block=obj_component.link_loose_material,
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

	def modal(self, context: Context, event: Event):  # pyright: ignore[reportIncompatibleMethodOverride]

		# Schedule a GUI redrawing to run after this modal function
		for a in context.screen.areas:
			a.tag_redraw()

		# Find the next step that needs work
		current_step: AF_PR_ImplementationImportStep | None = self.implementation.get_current_step()

		if current_step is not None:

			# Cancel the ongoing import process if ESC is pressed
			if event.type in {'ESC'}:
				current_step.state = AF_ImportActionState.canceled.value
				LOGGER.warning("USER_CANCEL")
				return {'CANCELLED'}

			# Cancel the ongoing import if the current step is already marked as canceled or failed
			# This mostly exists as a fallback because ideally the error would already be detected during execution and
			# then canceled immediately.
			if current_step.state in [AF_ImportActionState.failed.value, AF_ImportActionState.canceled.value]:
				LOGGER.warning(f"AUTO_CANCEL because {current_step.state}")
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

	def execute(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]

		# Initialize helpful variables
		self.af: AF_PR_AssetFetch = bpy.context.window_manager.af
		self.implementation_list: AF_PR_ImplementationList = self.af.current_implementation_list
		self.implementation: AF_PR_Implementation = self.implementation_list.implementations[self.af.current_implementation_list_index]
		self.asset_id: str = self.af.current_asset_list.assets[self.af.current_asset_list_index].name

		# Namespace for this import execution (used for loose material linking)
		self.af_namespace: str = str(uuid.uuid4())

		# Calculate the path for the temp directory
		self.temp_dir: str = os.path.join(tempfile.gettempdir(), "assetfetch-blender-temp-dl")

		# Variable to keep track of ongoing downloads
		self.ongoing_queries = {}

		# Lookup for functions to use
		self.step_functions = {
			AF_ImportAction.fetch_download.value: self.step_fetch_download,
			AF_ImportAction.fetch_from_zip_archive.value: self.step_fetch_from_zip_archive,
			AF_ImportAction.extract_zip_archive_fully.value: self.step_extract_zip_archive_fully,
			AF_ImportAction.import_obj_from_local_path.value: self.step_import_obj_from_local_path,
			AF_ImportAction.import_usd_from_local_path.value: self.step_import_usd_from_local_path,
			AF_ImportAction.import_blend_from_local_path.value: self.step_import_blend_from_local_path,
			AF_ImportAction.import_local_implementation_dir_to_blender_asset_library.value: self.step_import_local_implementation_dir_to_blender_asset_library,
			AF_ImportAction.import_loose_material_map_from_local_path.value: self.step_import_loose_material_map_from_local_path,
			AF_ImportAction.import_loose_environment_from_local_path.value: self.step_import_loose_environment_from_local_path,
			AF_ImportAction.unlock.value: self.step_unlock,
			AF_ImportAction.create_directory.value: self.step_create_directory,
			AF_ImportAction.delete_archive.value: self.step_delete_archive
		}

		# Clear the local implementation_directory
		self.clear_implementation_directory(self.implementation)

		# Reset the state of the implementation
		self.implementation.reset_state()

		# Set up modal operation
		self._timer = context.window_manager.event_timer_add(0.125, window=context.window)
		context.window_manager.modal_handler_add(self)

		# Return and hand of the real work to the modal function
		return {'RUNNING_MODAL'}
