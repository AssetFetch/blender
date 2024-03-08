import bpy

def register():
	bpy.utils.register_class(AF_PT_ProviderPanel)
	bpy.utils.register_class(AF_PT_AssetPanel)
	bpy.utils.register_class(AF_PT_ImplementationsPanel)
	

def unregister():
	bpy.utils.unregister_class(AF_PT_ImplementationsPanel)
	bpy.utils.unregister_class(AF_PT_AssetPanel)
	bpy.utils.unregister_class(AF_PT_ProviderPanel)
	

class AF_PT_ProviderPanel(bpy.types.Panel):
	bl_label = "Provider"
	bl_idname = "AF_PT_Provider_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		layout = self.layout

		# Add a text box to enter the URL
		layout.prop(context.window_manager, "af_initialize_provider_url", text="Provider URL")

		# Add a button to get the vendor info
		layout.operator("af.initialize_provider", text="Connect")
		
		layout.label(text=bpy.context.window_manager.af_initialize_provider_title)

		for provider_header in bpy.context.window_manager.af_initialize_provider_headers.values():
			layout.prop(provider_header,"value",text=provider_header["name"])


class AF_PT_AssetPanel(bpy.types.Panel):
	bl_label = "Assets"
	bl_idname = "AF_PT_ASSET_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		layout = self.layout

		# Query properties
		for asset_list_parameter in bpy.context.window_manager.af_asset_list_parameters.values():
			layout.prop(asset_list_parameter,"value",text=asset_list_parameter["name"])

		# Send button
		layout.operator("af.update_asset_list",text="Search Assets")

		# List of assets
			# Image
			# Title
			# (selectable)
		
		layout.template_list("UI_UL_list", "name", bpy.context.window_manager, "af_asset_list_entries", bpy.context.window_manager, "af_asset_list_entries_index")


class AF_PT_ImplementationsPanel(bpy.types.Panel):
	bl_label = "Implementations"
	bl_idname = "AF_PT_IMPLEMENTATIONS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		layout = self.layout

		if len(bpy.context.window_manager.af_asset_list_entries) > 0 and bpy.context.window_manager.af_asset_list_entries_index >= 0:
			# Query properties (if present)
			
			for asset_implementations_parameter in bpy.context.window_manager.af_asset_list_entries.values()[bpy.context.window_manager.af_asset_list_entries_index].implementations_query_parameters:
				layout.prop(asset_implementations_parameter,"value",text=asset_implementations_parameter["name"])

			# Send button
			layout.operator("af.update_implementations_list",text="Get File List")

			# Selection of implementations (if applicable)
			layout.template_list("UI_UL_list", "name", bpy.context.window_manager, "af_asset_implementations_options", bpy.context.window_manager, "af_asset_implementations_options_index")

			# Import plan
			import_plan_box = layout.box()
			import_plan_box.label(text="Import Plan will show up here...")
			# Import button
			layout.operator("af.execute_import_plan",text="Perform import")