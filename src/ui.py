import bpy

def register():
	for cl in registration_targets:
		bpy.utils.register_class(cl)
	
def unregister():
	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)
	

class AF_PT_ProviderPanel(bpy.types.Panel):
	bl_label = "Provider"
	bl_idname = "AF_PT_Provider_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		layout = self.layout
		af = bpy.context.window_manager.af

		# Add a text box to enter the URL
		layout.prop(context.window_manager.af, "current_init_url", text="Provider URL",icon="URL")

		# Add a button to get the vendor info
		layout.operator("af.initialize_provider", text="Initialize")
		
		# Title
		if af.current_provider_initialization.text.title != "":
			layout.label(text=af.current_provider_initialization.text.title,icon="PLUGIN")
		else:
			layout.label(text="(No title configured)",icon="PLUGIN")
		
		layout.label(text=af.current_provider_initialization.text.description)
		
		layout.separator()

		# Headers
		if len(af.current_provider_initialization.provider_configuration.headers.values() ) > 0:
			
			for provider_header in af.current_provider_initialization.provider_configuration.headers.values():
				layout.prop(provider_header,"value",text=provider_header.title)
			layout.operator("af.connection_status",text="Connect")

		connection_state_icons={
			"pending":"SEQUENCE_COLOR_09",
			"awaiting_input":"SEQUENCE_COLOR_03",
			"connection_error":"SEQUENCE_COLOR_01",
			"connected":"SEQUENCE_COLOR_04"
		}

		layout.label(text=af.current_connection_state.bl_rna.properties['state'].enum_items[af.current_connection_state.state].description,icon=connection_state_icons[af.current_connection_state.state])
		
		# Display user data
		if(af.current_connection_state.user.display_name != ""):
			layout.label(text=af.current_connection_state.user.display_name,icon="USER")
		if(af.current_connection_state.user.display_tier != ""):
			layout.label(text=af.current_connection_state.user.display_tier,icon="WORKSPACE")
		if(af.current_connection_state.unlock_balance.is_set):
			layout.label(text=f"{af.current_connection_state.unlock_balance.balance} {af.current_connection_state.unlock_balance.balance_unit}",icon="RADIOBUT_ON")



class AF_PT_AssetPanel(bpy.types.Panel):
	bl_label = "Assets"
	bl_idname = "AF_PT_ASSET_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		layout = self.layout
		af = bpy.context.window_manager.af

		# Query properties
		for asset_list_parameter in af.current_provider_initialization.asset_list_query.parameters.values():
			layout.prop(asset_list_parameter,"value",text=asset_list_parameter["name"])

		# Send button
		layout.operator("af.update_asset_list",text="Search Assets")

		# List of assets
			# Image
			# Title
			# (selectable)
		
		# Temporary icon test code:
		#icons_dict = bpy.utils.previews.new()
		#icons_dict.load("CAT_1","E:/Git/assetfetch-blender/tmp_icons/CAT_1.jpeg",'IMAGE')
		#layout.label(text="ASDF",icon_value=icons_dict['CAT_1'].icon_id)

		layout.template_list(listtype_name="UI_UL_list", list_id="asset_list", dataptr=bpy.context.window_manager.af.current_asset_list, propname="assets", active_dataptr=bpy.context.window_manager.af, active_propname="current_asset_list_index")
		
		
		



class AF_PT_ImplementationsPanel(bpy.types.Panel):
	bl_label = "Implementations"
	bl_idname = "AF_PT_IMPLEMENTATIONS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		return
		layout = self.layout

		if len(af_asset_list_entries) > 0 and af_asset_list_entries_index >= 0:
			# Query properties (if present)
			
			for asset_implementations_parameter in af_asset_list_entries.values()[af_asset_list_entries_index].implementations_query_parameters:
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

registration_targets = [
	AF_PT_ProviderPanel,
	AF_PT_AssetPanel,
	AF_PT_ImplementationsPanel
]