import random
import bpy
from ..property.core import *

class AF_PT_ImplementationsPanel(bpy.types.Panel):
	bl_label = "Implementations"
	bl_idname = "AF_PT_IMPLEMENTATIONS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'


	def format_bytes(self,num:int):
		for x in ['B','KB','MB','GB','TB']:
			if num < 1000.0:
				return "%3.1f %s" % (num, x)
			num /= 1000.0

	@classmethod
	def poll(self, context) -> bool:
		af  = bpy.context.window_manager.af 
		return af.current_connection_state.state == "connected" and len(af.current_asset_list.assets) > 0

	def draw(self, context):
		layout = self.layout
		af : AF_PR_AssetFetch = bpy.context.window_manager.af
		current_asset = af.current_asset_list.assets[af.current_asset_list_index]

		# Query properties
		current_asset.implementation_list_query.draw_ui(layout)

		#layout.operator("af.update_implementations_list",text="Search Implementations")

		# Create default import button label
		import_button_label = "Import"
		
		# We have results to display...
		if len(af.current_implementation_list.implementations) > 0:

			# Selection of implementations (if applicable)
			layout.template_list("UI_UL_list", "name", af.current_implementation_list, "implementations", af, "current_implementation_list_index")

			current_impl : AF_PR_Implementation = af.get_current_implementation()
			current_step : AF_PR_ImplementationImportStep = current_impl.get_current_step()

			# Import button
			layout.operator("af.execute_import_plan",text=import_button_label)

			# Confirm readability
			if current_impl.is_valid:
				layout.label(text="Implementation is readable. Ready to import.",icon="SEQUENCE_COLOR_04")
				if current_impl.expected_charges > 0:
					import_button_label = f"Import ({current_impl.expected_charges} {af.current_connection_state.unlock_balance.balance_unit})"
			else:
				layout.label(text="Implementation is not readable.",icon="SEQUENCE_COLOR_01")

			layout.separator()

			#layout.label(text=f"{current_impl.get_completed_step_count()} / {current_impl.get_step_count()} steps completed.")

			#layout.separator()

			# Import progress:

			previous_step_action = None
			for step in current_impl.import_steps:
				
				# Prepare variables for rendering the UI
				step : AF_PR_ImplementationImportStep = step
				step_title = step.bl_rna.properties['action'].enum_items[step.action].name
				step_action_icon = AF_ImportAction[step.action].icon_string()
				step_state_icon =  AF_ImportActionState[step.state].icon_string()

				# Check whether a new box must be drawn
				if step.action != previous_step_action:
					box = layout.box()
					box.label(text=step_title,icon=step_action_icon)

				# Create a new row in the current box
				row = box.row()

				if step.state in [AF_ImportActionState.canceled.value,AF_ImportActionState.failed.value]:
					row.alert = True

				# Display details about the current step
				step_details = "<No Details> "

				# Download
				if step.action == AF_ImportAction.fetch_download.value:
					target_component = current_impl.get_component_by_id(step.config['component_id'].value)
					step_details = target_component.file_handle.local_path
					target_length = target_component.file_info.length
					if target_length > 0:
						step_details += f" - {self.format_bytes(target_length)}"
				if step.action in [AF_ImportAction.fetch_from_zip_archive.value,AF_ImportAction.import_obj_from_local_path.value,AF_ImportAction.import_usd_from_local_path.value]:
					target_component = current_impl.get_component_by_id(step.config['component_id'].value)
					step_details = target_component.file_handle.local_path
				if step.action == AF_ImportAction.import_loose_material_map_from_local_path.value:
					target_component = current_impl.get_component_by_id(step.config['component_id'].value)
					target_path = target_component.file_handle.local_path
					target_material = target_component.loose_material_define.material_name
					target_map = target_component.loose_material_define.map
					step_details = f"{target_path} → {target_material}/{target_map}"
				if step.action == AF_ImportAction.create_directory.value:
					step_details = step.config['directory'].value


				# Display a static icon or a progress indicator for the current step
				if step.completion > 0.0 and step.completion < 1.0 and step.state not in [AF_ImportActionState.canceled.value,AF_ImportActionState.failed.value]:
					row.progress(text=step_details,factor=step.completion,type="RING")
				else:
					row.label(text=step_details,icon=step_state_icon)

				# Remember the action type of this step
				previous_step_action = step.action

			for m in current_impl.validation_messages:
				layout.label(text=m.text)
			

			
			
		
		# We have already queried and found that there are no results...
		elif af.current_implementation_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No implementations found for this query.",icon="ORPHAN_DATA")