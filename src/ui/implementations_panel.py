import random
import bpy
from ..property.core import *


class AF_UL_ImplementationsItems(bpy.types.UIList):
	"""Class for drawing the list of implementations."""

	def draw_item(self, context, layout: bpy.types.UILayout, data, item: AF_PR_Implementation, icon, active_data, active_propname, index):

		# Add colored icon to quickly indicate if an implementation is readable
		if item.is_valid:
			icon = "SEQUENCE_COLOR_04"
		else:
			icon = "SEQUENCE_COLOR_01"

		# Render the name of the implementation
		row = layout.row()
		if item.text.is_set:
			row.label(text=item.text.title, icon=icon)
		else:
			row.label(text=item.name, icon=icon)


class AF_PT_ImplementationsPanel(bpy.types.Panel):
	"""Class for drawing the implementations panel ('Import Settings' in the UI)."""

	bl_label = "Import Settings"
	bl_idname = "AF_PT_IMPLEMENTATIONS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def format_bytes(self, num: int):
		"""Formats a number of bytes in the appropriate unit."""
		for x in ['B', 'KB', 'MB', 'GB', 'TB']:
			if num < 1000.0:
				return "%3.1f %s" % (num, x)
			num /= 1000.0

	@classmethod
	def poll(self, context) -> bool:
		af = bpy.context.window_manager.af
		return af.current_connection_state.state == "connected" and len(af.current_asset_list.assets) > 0

	def strike_through_text(self, text: str):
		"""Create a strike-through effect on the given text using unicode."""
		result = ''
		for c in text:
			result = result + c + '\u0336'
		return result

	def draw(self, context):

		# Helpful variables
		layout = self.layout
		af: AF_PR_AssetFetch = bpy.context.window_manager.af
		current_asset = af.current_asset_list.assets[af.current_asset_list_index]

		# Draw the form for querying implementations
		current_asset.implementation_list_query.draw_ui(layout)

		# We have results to display...
		if len(af.current_implementation_list.implementations) > 0:

			layout.separator()

			# Selection of implementations
			if len(af.current_implementation_list.implementations) > 1:
				layout.template_list(listtype_name="AF_UL_ImplementationsItems",
					list_id="name",
					dataptr=af.current_implementation_list,
					propname="implementations",
					active_dataptr=af,
					active_propname="current_implementation_list_index",
					sort_lock=True,
					rows=3)

			current_impl: AF_PR_Implementation = af.get_current_implementation()
			current_step: AF_PR_ImplementationImportStep = current_impl.get_current_step()

			import_info_box = layout.box()

			# Calculate how to display the charges

			# charges_full -> Charges that would apply if no unlocking query was already activated
			# charges_actual -> Charges that will actually apply if the import is performed
			charges_full = current_impl.get_expected_charges(include_already_paid=True)
			charges_actual = current_impl.get_expected_charges(include_already_paid=False)

			# Render only the full price if it reflects the actual price...
			if charges_full == charges_actual:
				if charges_full > 0:
					row = import_info_box.row()
					row.label(text="Price")
					row.label(text=f"{charges_actual} {af.current_connection_state.unlock_balance.balance_unit}")

			# Render the original and the reduced price if the actual price is below the full price
			else:
				charges_formatted = f"{self.strike_through_text(str(charges_full))} {charges_actual} {af.current_connection_state.unlock_balance.balance_unit}"
				row = import_info_box.row()
				row.label(text="Price")
				row.label(text=charges_formatted)

			# Render download information
			row = import_info_box.row()
			row.label(text="Download Size")
			row.label(text=self.format_bytes(current_impl.get_download_size()))

			# Render validation messages in GUI
			for m in current_impl.validation_messages:
				validation_message_row = layout.row()
				validation_message_row.alert = True
				validation_message_row.label(text=m.text)

			# Import button
			if current_impl.get_completed_step_count() > 0 and not current_impl.all_steps_completed():
				import_button_label = "Importing..."
			else:
				if charges_actual > 0.0:
					import_button_label = "Pay & Perform Import"
				else:
					import_button_label = "Perform Import"

			# Render the import button
			import_button_row = layout.row()
			if current_impl.get_current_state() == AF_ImportActionState.running:
				import_button_row.enabled = False
			import_button_row.operator("af.execute_import_plan", text=import_button_label)

			layout.separator()

			if current_impl.is_valid and len(current_impl.import_steps) > 0:
				layout.label(text=f"Import Steps ({current_impl.get_completed_step_count()} / {current_impl.get_step_count()} completed):")

				previous_step_action = None
				for step in current_impl.import_steps:

					# Prepare variables for rendering the UI
					step: AF_PR_ImplementationImportStep = step
					step_title = step.bl_rna.properties['action'].enum_items[step.action].name
					step_action_icon = AF_ImportAction[step.action].icon_string()
					step_state_icon = AF_ImportActionState[step.state].icon_string()

					# Check whether a new box must be drawn
					if step.action != previous_step_action:
						box = layout.box()
						box.label(text=step_title, icon=step_action_icon)

					# Create a new row in the current box
					row = box.row()

					if step.state in [AF_ImportActionState.canceled.value, AF_ImportActionState.failed.value]:
						row.alert = True

					# Display details about the current step
					step_details = "<No Details> "

					# Download
					if step.action == AF_ImportAction.fetch_download.value:
						target_component = current_impl.get_component_by_id(step.config['component_id'].value)
						step_details = target_component.store.local_file_path
						target_length = target_component.store.bytes
						if target_length > 0:
							step_details += f" - {self.format_bytes(target_length)}"

					# Standard imports
					if step.action in [
						AF_ImportAction.fetch_from_zip_archive.value, AF_ImportAction.import_obj_from_local_path.value, AF_ImportAction.import_usd_from_local_path.value
					]:
						target_component = current_impl.get_component_by_id(step.config['component_id'].value)
						step_details = target_component.store.local_file_path

					# Loose materials
					if step.action == AF_ImportAction.import_loose_material_map_from_local_path.value:
						target_component = current_impl.get_component_by_id(step.config['component_id'].value)
						target_path = target_component.store.local_file_path
						target_material = target_component.handle_loose_material_map.material_name
						target_map = target_component.handle_loose_material_map.map
						step_details = f"{target_path} → {target_material}/{target_map}"

					# Loose environment
					if step.action == AF_ImportAction.import_loose_environment_from_local_path.value:
						target_component = current_impl.get_component_by_id(step.config['component_id'].value)
						target_path = target_component.store.local_file_path
						step_details = f"Import {target_path}"

					# Unlocking
					if step.action == AF_ImportAction.unlock.value:
						query_id = step.config['query_id']
						unlock_query: AF_PR_UnlockQuery = bpy.context.window_manager.af.current_implementation_list.get_unlock_query_by_id(query_id)
						step_details = f"Unlock content ({unlock_query.price} {af.current_connection_state.unlock_balance.balance_unit})"

					# Directories
					if step.action == AF_ImportAction.create_directory.value:
						step_details = step.config['directory'].value

					# Display a static icon or a progress indicator for the current step
					if step.completion > 0.0 and step.completion < 1.0 and step.state not in [AF_ImportActionState.canceled.value, AF_ImportActionState.failed.value]:
						row.progress(text=step_details, factor=step.completion, type="RING")
					else:
						row.label(text=step_details, icon=step_state_icon)

					# Remember the action type of this step
					previous_step_action = step.action

		# We have already queried and found that there are no results...
		elif af.current_implementation_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No implementations found for this query.", icon="ORPHAN_DATA")
