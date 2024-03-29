import bpy

class AF_PT_ImplementationsPanel(bpy.types.Panel):
	bl_label = "Implementations"
	bl_idname = "AF_PT_IMPLEMENTATIONS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	@classmethod
	def poll(self, context) -> bool:
		af  = bpy.context.window_manager.af 
		return len(af.current_asset_list.assets) > 0

	def draw(self, context):
		layout = self.layout
		af = bpy.context.window_manager.af
		current_asset = af.current_asset_list.assets[af.current_asset_list_index]

		# Query properties
		current_asset.implementation_list_query.draw_ui(layout)

		layout.operator("af.update_implementations_list",text="Search Implementations")
		
		if len(af.current_implementation_list.implementations) > 0:

			# Selection of implementations (if applicable)
			layout.template_list("UI_UL_list", "name", af.current_implementation_list, "implementations", af, "current_implementation_list_index")

			current_impl  = af.current_implementation_list.implementations[af.current_implementation_list_index]

			# Import plan
			if current_impl.is_valid:
				layout.label(text="Implementation is readable. Ready to import.",icon="SEQUENCE_COLOR_04")
				
			else:
				layout.label(text="Implementation is not readable.",icon="SEQUENCE_COLOR_01")
		elif af.current_implementation_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No implementations found for this query.",icon="ORPHAN_DATA")

		# Import button
		layout.operator("af.execute_import_plan",text="Import")