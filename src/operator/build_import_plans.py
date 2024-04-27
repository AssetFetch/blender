import bpy,os
from ..util.addon_constants import AF_ImportAction

class AF_OP_BuildImportPlans(bpy.types.Operator):
	"""Populates every currently loaded implementation with a plan for how to import them, if possible."""
	
	bl_idname = "af.build_import_plans"
	bl_label = "Build Import Plans"
	bl_options = {"REGISTER"}

	def execute(self,context):
		af  = bpy.context.window_manager.af

		for current_impl in af.current_implementation_list.implementations:
			# Enter try-catch block
			# Failing this block causes an implementation to be considered unreadable.
			# If it passes, it is considered readable.
			
			try:
				
				# We start by assuming that the implementation is valid and make sure that it is empty
				current_impl.is_valid = True
				current_impl.import_steps.clear()
				current_impl.expected_charges = 0

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

				current_impl.import_steps.add().set_action(AF_ImportAction.directory_create).set_config_value("directory",current_impl.local_directory)

				# Step 2: Find the relevant unlocking queries
				already_scheduled_unlocking_query_ids = []
				for comp in current_impl.components:
					if comp.unlock_link.is_set:
						referenced_query  = af.current_implementation_list.get_unlock_query_by_id(comp.unlock_link.unlock_query_id)
						if (not referenced_query.unlocked) and (referenced_query.name not in already_scheduled_unlocking_query_ids):
							current_impl.import_steps.add().set_action(AF_ImportAction.unlock).set_config_value("query_id",comp.unlock_link.unlock_query_id)
							already_scheduled_unlocking_query_ids.append(comp.unlock_link.unlock_query_id)		
							current_impl.expected_charges += referenced_query.price

				# Step 3: Plan how to acquire and arrange all files in the asset directory
				already_processed_component_ids = set()
				
				def recursive_fetching_datablock_handler(comp ):

					# Keep track of which components were already processed
					if comp.name in already_processed_component_ids:
						return
					else:
						already_processed_component_ids.add(comp.name)
					
					# Decide how to handle this component (recursively if it references an archive)
					if comp.file_fetch_download.is_set:
						current_impl.import_steps.add().set_action(AF_ImportAction.fetch_download).set_config_value("component_id",comp.name)
					elif comp.file_fetch_from_archive.is_set:
						target_comp = next(c for c in current_impl.components if c.name == comp.file_fetch_from_archive.archive_component_id)
						if not target_comp:
							raise Exception(f"Referenced component {comp.file_fetch_from_archive.archive_component_id} could not be found.")
						recursive_fetching_datablock_handler(target_comp)
						current_impl.import_steps.add().set_action(AF_ImportAction.fetch_from_zip_archive).set_config_value("component_id",comp.name)
					elif comp.unlock_link.is_set:
						current_impl.import_steps.add().set_action(AF_ImportAction.fetch_from_zip_archive).set_config_value("component_id",comp.name)
						current_impl.import_steps.add().set_action(AF_ImportAction.fetch_download).set_config_value("component_id",comp.name)
					else:
						raise Exception(f"{comp.name} is missing either a file_fetch.download, file_fetch.from_archive or unlock_link datablock.")

				for comp in current_impl.components:
					recursive_fetching_datablock_handler(comp)
					

				# Step 4: Plan how to import main model file
				# "Importing" includes loading the file using the software's native format handler
				# and creating or applying loose materials referenced in loose_material datablocks
				for comp in current_impl.components:
					if comp.file_handle.behavior == "single_active":
						if comp.file_info.extension == ".obj":
							current_impl.import_steps.add().set_action(AF_ImportAction.import_obj_from_local_path).set_config_value("component_id",comp.name)
						if comp.file_info.extension in [".usd",".usda",".usdc",".usdz"]:
							current_impl.import_steps.add().set_action(AF_ImportAction.import_usd_from_local_path).set_config_value("component_id",comp.name)

				# Step 5: Plan how to import other files, such as loose materials
				for comp in current_impl.components:
					if comp.loose_material_define.is_set:
						current_impl.import_steps.add().set_action(AF_ImportAction.import_loose_material_map_from_local_path).set_config_value("component_id",comp.name)


			except Exception as e:
				current_impl.is_valid = False
				current_impl.validation_messages.add().set("crit",str(e))
				raise e
		return {'FINISHED'}