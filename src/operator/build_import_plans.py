import bpy, os
from ..util.addon_constants import *
from ..util.af_constants import *
from ..property.core import *


class AF_OP_BuildImportPlans(bpy.types.Operator):
	"""Populates every currently loaded implementation with a plan for how to import it, if possible."""

	# Standard metadata
	bl_idname = "af.build_import_plans"
	bl_label = "Build Import Plans"
	bl_options = {"REGISTER", "INTERNAL"}

	#def __init__(self) -> None:
	#	self.already_processed_component_ids = set()
	#	self.current_impl: AF_PR_Implementation = None

	def execute(self, context):
		af: AF_PR_AssetFetch = bpy.context.window_manager.af

		# Loop over all currently loaded implementations
		for current_impl in af.current_implementation_list.implementations:

			# Enter try-catch block
			# Failing this block causes an implementation to be considered unreadable.
			# If it passes, it is considered readable.

			try:

				# Step 0: Set/create helpful variables

				# Keeps track of which components were already processed.
				# This becomes an interesting question when recursively resolving dependencies, for example when working with archives.
				already_processed_component_ids = set()

				# Keeps track of which of the unlocking queries offered by the provider are already scheduled to be called for this implementation.
				already_scheduled_unlocking_query_ids = set()

				# Other useful shorthands
				provider_id = af.current_provider_initialization.name
				asset_id = af.current_asset_list.assets[af.current_asset_list_index].name
				implementation_id = current_impl.name

				if provider_id == "":
					raise Exception("No provider ID to create implementation directory.")
				if asset_id == "":
					raise Exception("No asset ID to create implementation directory.")
				if implementation_id == "":
					raise Exception("No implementation ID to create implementation directory.")

				# We start by assuming that the implementation is valid, has no existing steps and costs nothing.
				current_impl.is_valid = True
				current_impl.import_steps.clear()

				# Step 1: Find the implementation directory - Where should all the downloaded files for this implementation be stored?

				# Start with the base directory and append the provider/asset/implementation structure to it
				local_directory = AF_PR_Preferences.get_prefs().get_current_download_directory()
				local_directory = os.path.join(local_directory, provider_id)
				local_directory = os.path.join(local_directory, asset_id)
				local_directory = os.path.join(local_directory, implementation_id)
				current_impl.local_directory = local_directory

				# Register the step to create the directory
				current_impl.import_steps.add().configure_create_directory(current_impl.local_directory)

				# Step 2: Find the relevant unlocking queries - Which unlockings/purchases need to be made with the provider in order to use this implementation?
				for comp in current_impl.components:

					# Is this a component that requires unlocking?
					if comp.file_fetch_download_post_unlock.is_set:

						unlocking_query_id = comp.file_fetch_download_post_unlock.unlock_query_id

						# Get the unlocking query that this component is linked to
						referenced_query = af.current_implementation_list.get_unlock_query_by_id(unlocking_query_id)

						# Test if the query is already unlocked or already scheduled to be unlocked.
						# Otherwise schedule it.
						if (not referenced_query.unlocked) and (referenced_query.name not in already_scheduled_unlocking_query_ids):

							# Create new step for performing the unlocking query
							unlocking_step = current_impl.import_steps.add()
							unlocking_step.configure_unlock(unlocking_query_id)

							# Add the query id to the set of already scheduled queries
							already_scheduled_unlocking_query_ids.add(unlocking_query_id)

				# Step 3: Get all the previously withheld datablocks
				for comp in current_impl.components:
					if comp.file_fetch_download_post_unlock.is_set:

						# This schedules the query to obtain the real download link
						# which the provider only hands out after the asset has already been unlocked and which may be ephemeral.
						current_impl.import_steps.add().configure_unlock_get_download_data(comp.name)

				# Step 4: Download all files
				# After the preparations in steps 2 and 3 (if those were even required) the actual file download can now be scheduled.
				for comp in current_impl.components:
					if comp.file_fetch_download.is_set or comp.file_fetch_download_post_unlock.is_set:

						# This schedules the actual file download using the HTTP query that was either there in the first place or
						# which has been obtained during a previous step.
						current_impl.import_steps.add().configure_fetch_download(comp.name)

				# Step 5: Extract files from archives
				# If the implementation makes use of archives for data transfer then the files must be unpacked.
				# This must happen in proper order to ensure that unpacking works even if the provider is sending nested ZIP files
				# (Yes, this is actually a thing sometimes!)

				# This list contains all the components that need to be extracted from an archive
				pending_extraction_comps = []
				for comp in current_impl.components:
					# Does the component have the "file_fetch.from_archive" datablock? If yes: Add it to the list
					if comp.file_fetch_from_archive.is_set:
						pending_extraction_comps.append(comp)

				# Work through the list and process the components.
				# Components are removed from the list afterwards.
				#
				while len(pending_extraction_comps) > 0:
					scheduled_in_this_iteration = 0
					for pcomp in pending_extraction_comps:

						# Get the target archive component that the current component lists as its source.
						source_archive_comp_id = pcomp.file_fetch_from_archive.archive_component_id
						source_archive_comp = current_impl.get_component_by_id(source_archive_comp_id)
						if not source_archive_comp:
							raise Exception(f"Referenced component {source_archive_comp_id} could not be found.")

						if source_archive_comp in pending_extraction_comps:
							# The target is still pending, we can't schedule with this one yet and need to revisit it during the next iteration.
							continue
						else:
							# The referenced component is not pending (anymore or never in the first place), so we can schedule
							# the extraction and remove this one from the list of pending components.
							current_impl.import_steps.add().configure_fetch_from_zip_archive(pcomp.name)
							pending_extraction_comps.remove(pcomp)
							scheduled_in_this_iteration += 1

					# Doing a full iteration without being able to schedule a single component indicates that the remaining components are unreachable.
					# This is a failure state.
					if scheduled_in_this_iteration < 1:
						unreachable_components_formatted = ""
						for pcomp in pending_extraction_comps:
							unreachable_components_formatted += pcomp.name + " "
						raise Exception(f"Components {unreachable_components_formatted} could not be resolved in the provided implementation definition.")

				# Step 4: Plan how to import files
				# "Importing" includes loading the file using Blender's native format handler
				# and creating or applying loose materials referenced in loose_material.* datablocks

				# This is the list of extensions that should be treated as material maps (if they have the loose_material.define datablock)
				for comp in current_impl.components:

					# Material maps and HDRIs get a completely separate treatment
					if comp.loose_material_define.is_set:
						if comp.file_handle.behavior == "single_active":
							# The component has the material definition datablock AND is marked as active, so it certainly needs to be imported.
							current_impl.import_steps.add().configure_import_loose_material_map_from_local_path(comp.name)
						else:

							# The component does have the material definition datablock but is marked as passive.
							# According to the rules of AssetFetch, it should only be imported, if it is referenced by another component
							import_map = False
							for c in current_impl.components:
								if c.loose_material_apply.is_set:
									for m in c.loose_material_apply.items:
										if m.material_name == comp.loose_material_define.material_name:
											import_map = True

							if import_map:
								current_impl.import_steps.add().configure_import_loose_material_map_from_local_path(comp.name)

					elif comp.loose_environment.is_set and comp.file_handle.behavior == "single_active" :
						
						if comp.file_info.extension not in ['.exr','.hdr']:
							raise Exception(f"The addon does not know how to handle HDRI environments with the extension '{comp.file_info.extension}'.")

						if comp.loose_environment.projection != "equirectangular":
							raise Exception("The addon currently only supports HDRIs with equirectangular projection.")

						current_impl.import_steps.add().configure_import_loose_environment_from_local_path(comp.name)

					# Handle all other files
					elif comp.file_handle.behavior == "single_active":

						# OBJ Model
						if comp.file_info.extension == ".obj":
							current_impl.import_steps.add().configure_import_obj_from_local_path(comp.name)

						# USD Files
						elif comp.file_info.extension in [".usd", ".usda", ".usdc", ".usdz"]:
							current_impl.import_steps.add().configure_import_usd_from_local_path(comp.name)

						# TODO: More extensions to be added here in the future

						else:
							raise Exception(f"The addon does not know how to actively handle this '{comp.file_info.extension}'-file using the given metadata.")

			except Exception as e:
				current_impl.is_valid = False
				current_impl.validation_messages.add().set("crit", str(e))
				raise e
		return {'FINISHED'}
