import bpy

class AF_PT_ProviderPanel(bpy.types.Panel):
	bl_label = "Provider"
	bl_idname = "AF_PT_Provider_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		layout = self.layout
		af = bpy.context.window_manager.af

		# Info Box
		info_box = layout.box()

		info_box.label(text="AssetFetch for Blender v0.1.0-alpha.",icon="SETTINGS")
		info_box.label(text=f"Download directory: {af.download_directory}")
		info_box.label(text="Unstable & lacking numerous features, use with caution & patience!")

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
