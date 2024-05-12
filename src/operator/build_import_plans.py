import bpy, os
from ..util.addon_constants import *
from ..util.af_constants import *
from ..property.core import *


class AF_OP_BuildImportPlans(bpy.types.Operator):
	"""Populates every currently loaded implementation with a plan for how to import them, if possible."""

	bl_idname = "af.build_import_plans"
	bl_label = "Build Import Plans"
	bl_options = {"REGISTER", "INTERNAL"}

	def __init__(self) -> None:
		self.already_processed_component_ids = set()
		self.current_impl: AF_PR_Implementation = None

	def execute(self, context):
		af = bpy.context.window_manager.af

		for i in af.current_implementation_list.implementations:

			# Enter try-catch block
			# Failing this block causes an implementation to be considered unreadable.
			# If it passes, it is considered readable.

			try:

				# Step 0: Set/create helpful variables
				self.current_impl = i
				self.already_processed_component_ids = set()

				provider_id = af.current_provider_initialization.name
				asset_id = af.current_asset_list.assets[af.current_asset_list_index].name
				implementation_id = self.current_impl.name

				# We start by assuming that the implementation is valid, has no existing steps and costs nothing.
				self.current_impl.is_valid = True
				self.current_impl.import_steps.clear()
				self.current_impl.expected_charges = 0

				# Step 1: Find the implementation directory
				if provider_id == "":
					raise Exception("No provider ID to create implementation directory.")
				if asset_id == "":
					raise Exception("No asset ID to create implementation directory.")
				if implementation_id == "":
					raise Exception("No implementation ID to create implementation directory.")

				self.current_impl.local_directory = os.path.join(af.download_directory, provider_id)
				self.current_impl.local_directory = os.path.join(self.current_impl.local_directory, asset_id)
				self.current_impl.local_directory = os.path.join(self.current_impl.local_directory, implementation_id)

				self.current_impl.import_steps.add().configure_create_directory(self.current_impl.local_directory)

				# Step 2: Find the relevant unlocking queries
				already_scheduled_unlocking_query_ids = set()
				for comp in self.current_impl.components:
					if comp.file_fetch_download_post_unlock.is_set:
						referenced_query = af.current_implementation_list.get_unlock_query_by_id(comp.file_fetch_download_post_unlock.unlock_query_id)
						if (not referenced_query.unlocked) and (referenced_query.name not in already_scheduled_unlocking_query_ids):
							self.current_impl.import_steps.add().configure_unlock(comp.file_fetch_download_post_unlock.unlock_query_id)
							already_scheduled_unlocking_query_ids.append(comp.file_fetch_download_post_unlock.unlock_query_id)
							self.current_impl.expected_charges += referenced_query.price

				# Step 3: Get all the previously withheld datablocks
				for comp in self.current_impl.components:
					if comp.file_fetch_download_post_unlock.is_set:
						self.current_impl.import_steps.add().configure_unlock_get_download_data(comp.name)

				# Step 4: Download all files
				for comp in self.current_impl.components:
					if comp.file_fetch_download.is_set or comp.file_fetch_download_post_unlock.is_set:
						self.current_impl.import_steps.add().configure_fetch_download(comp.name)

				# Step 5: Extract files from archives
				pending_extraction_comps = []

				# 5.1: Get all the components that actually need to be extracted from a zip
				for comp in self.current_impl.components:
					if comp.file_fetch_from_archive.is_set:
						pending_extraction_comps.append(comp)

				while len(pending_extraction_comps) > 0:
					for pcomp in pending_extraction_comps:
						# Get the target archive component ...
						target_archive_comp = self.current_impl.get_component_by_id(pcomp.file_fetch_from_archive.archive_component_id)
						if not target_archive_comp:
							raise Exception(f"Referenced component {pcomp.file_fetch_from_archive.archive_component_id} could not be found.")

						if target_archive_comp in pending_extraction_comps:
							# The target is still pending, we can't continue with this one yet
							continue
						else:
							self.current_impl.import_steps.add().configure_fetch_from_zip_archive(comp.name)
							pending_extraction_comps.remove(pcomp)

				# Step 4: Plan how to import active files
				# "Importing" includes loading the file using the software's native format handler
				# and creating or applying loose materials referenced in loose_material datablocks
				for comp in self.current_impl.components:

					# Common 3D formats which are only handled if they are marked as active
					if comp.file_handle.behavior == "single_active":

						# OBJ Model
						if comp.file_info.extension == ".obj":
							self.current_impl.import_steps.add().configure_import_obj_from_local_path(comp.name)

						# USD Files
						elif comp.file_info.extension in [".usd", ".usda", ".usdc", ".usdz"]:
							self.current_impl.import_steps.add().configure_import_usd_from_local_path(comp.name)

						# Material maps
						elif comp.file_info.extension in [".png", ".jpg", ".tiff"]:
							self.material_map_handler(comp)

						else:
							raise Exception(f"The addon does not know how to actively handle files with the extension '{comp.file_info.extension}'.")

			except Exception as e:
				self.current_impl.is_valid = False
				self.current_impl.validation_messages.add().set("crit", str(e))
				raise e
		return {'FINISHED'}

	def material_map_handler(self, comp):
		if comp.loose_material_define.is_set and comp.file_handle.behavior == "single_active":
			# The component has the material definition datablock AND is marked as active, so it certainly needs
			# to be imported.
			self.current_impl.import_steps.add().configure_import_loose_material_map_from_local_path(comp.name)

		elif comp.loose_material_define.is_set:
			# The component does have the material definition datablock but is marked as passive.
			# According to the rules of AF, it should only be imported, if it is referenced by another component
			import_map = False
			for c in self.current_impl.components:
				if c.loose_material_apply.is_set:
					for m in c.loose_material_apply.items:
						if m.material_name == comp.loose_material_define.material_name:
							import_map = True

			if import_map:
				self.current_impl.import_steps.add().configure_import_loose_material_map_from_local_path(comp.name)

		else:
			raise Exception(f"This {comp.file_info.extension} image file does not have the required metadata to be readable.")

	def recursive_fetching_datablock_handler(self, comp):

		# Keep track of which components were already processed
		if comp.name in self.already_processed_component_ids:
			return
		else:
			self.already_processed_component_ids.add(comp.name)

		if comp.file_fetch_download.is_set:

			# Case 1
			# Simplest case: It's a single file download and the download information is already there. Done!
			self.current_impl.import_steps.add().configure_fetch_download(comp.name)

		elif comp.file_fetch_from_archive.is_set:

			# Case 2
			# This component must be loaded from an archive, so we resolve it and handle it first (if necessary),
			# so that all files from archives are only loaded AFTER the archive itself has been downloaded.

			# Get the target archive component ...
			target_archive_comp = self.current_impl.get_component_by_id(comp.file_fetch_from_archive.archive_component_id)
			if not target_archive_comp:
				raise Exception(f"Referenced component {comp.file_fetch_from_archive.archive_component_id} could not be found.")

			# ...and handle it through the dedicated function which inserts the required import steps.
			self.recursive_fetching_datablock_handler(target_archive_comp)

			# Then add the step that loads the actual file we want from the archive
			self.current_impl.import_steps.add().configure_fetch_from_zip_archive(comp.name)

		elif comp.file_fetch_download_post_unlock.is_set:

			# Case 3
			# The component is not quite ready for an immediate download
			# We first need to get the real fetch_download block from the provider

			self.current_impl.import_steps.add().configure_unlock_get_download_data(comp.name)
			self.current_impl.import_steps.add().configure_fetch_download(comp.name)
		else:
			raise Exception(f"{comp.name} is missing either a file_fetch.* datablock.")
