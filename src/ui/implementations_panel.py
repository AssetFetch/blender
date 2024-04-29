import random
import bpy
from ..property.core import *

class AF_PT_ImplementationsPanel(bpy.types.Panel):
	bl_label = "Implementations"
	bl_idname = "AF_PT_IMPLEMENTATIONS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	@classmethod
	def poll(self, context) -> bool:
		af  = bpy.context.window_manager.af 
		return af.current_connection_state.state == "connected" and len(af.current_asset_list.assets) > 0

	def draw(self, context):
		layout = self.layout
		af = bpy.context.window_manager.af
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

			# Confirm readability
			if current_impl.is_valid:
				layout.label(text="Implementation is readable. Ready to import.",icon="SEQUENCE_COLOR_04")
				if current_impl.expected_charges > 0:
					import_button_label = f"Import ({current_impl.expected_charges} {af.current_connection_state.unlock_balance.balance_unit})"
			else:
				layout.label(text="Implementation is not readable.",icon="SEQUENCE_COLOR_01")

			# Import button
			layout.operator("af.execute_import_plan",text=import_button_label)

			layout.separator()

			# Import progress:

			for step in current_impl.import_steps:
				step : AF_PR_ImplementationImportStep = step
				step_entry_row = layout.row()
				step_icon =  AF_ImportActionState[step.state].icon_string()
				step_entry_row.label(text="",icon=step_icon)
				step_entry_col = step_entry_row.column()

				step_entry_title = step.get_action_title()

				if step.completion > 0.0 and step.completion < 1.0:
					step_entry_title += f" ({int(step.completion*100)}%)"

				step_entry_col.label(text=step_entry_title)
				step_entry_col.label(text=step.get_action_config())
			for m in current_impl.validation_messages:
				layout.label(text=m.text)
			

			
			
		
		# We have already queried and found that there are no results...
		elif af.current_implementation_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No implementations found for this query.",icon="ORPHAN_DATA")