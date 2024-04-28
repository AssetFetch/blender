import bpy


class AF_PT_ImportStepsPanel(bpy.types.Panel):
	bl_label = "Import Details"
	bl_idname = "AF_PT_IMPORT_STEPS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	@classmethod
	def poll(self, context) -> bool:
		af  = bpy.context.window_manager.af 
		return af.current_connection_state.state == "connected" and len(af.current_implementation_list.implementations) > 0

	def draw(self, context):
		layout = self.layout
		af  = bpy.context.window_manager.af
		current_impl  = af.current_implementation_list.implementations[af.current_implementation_list_index]
		for step in current_impl.import_steps:
			step_box = layout.box()
			step_box.label(text=step.get_action_title())
			step_box.label(text=step.get_action_config())
			step_box.label(text=step.state)
		for m in current_impl.validation_messages:
			layout.label(text=m.text)
