import bpy
from ..property.preferences import *

class AF_PT_ProviderPanel(bpy.types.Panel):
	"""Class for rendering the provider selection panel."""

	bl_label = "Provider Connection"
	bl_idname = "AF_PT_Provider_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	def draw(self, context):
		layout = self.layout
		af = bpy.context.window_manager.af

		# Info Box
		#info_box = layout.box()
		#info_box.label(text="AssetFetch for Blender v0.2.0", icon="SETTINGS")
		#info_box.label(text=f"Download directory: {af.download_directory}")
		#info_box.label(text=f"Icon directory: {af.ui_image_directory}")
		#info_box.label(text="Unstable & lacking numerous features, use with caution & patience!")

		# Bookmarks
		layout.prop(af,"provider_bookmark_selection")

		# Initialization URL
		row = layout.row()
		if "provider_bookmark_selection" in af and af['provider_bookmark_selection'] > 0:
			row.enabled = False
		row.prop(context.window_manager.af, "current_init_url", text="Provider URL", icon="URL")

		# Headers
		if len(af.current_provider_initialization.provider_configuration.headers.values()) > 0:
			for provider_header in af.current_provider_initialization.provider_configuration.headers.values():
				col = layout.column()
				col.prop(provider_header, "value", text=provider_header.title)
				#layout.operator("af.connection_status",text="Connect")
				if af['provider_bookmark_selection'] > 0:
					col.enabled = False

		# Connection state
		connection_state_icons = {"pending": "SEQUENCE_COLOR_09", "awaiting_input": "SEQUENCE_COLOR_03", "connection_error": "SEQUENCE_COLOR_01", "connected": "SEQUENCE_COLOR_04"}

		layout.label(text=af.current_connection_state.bl_rna.properties['state'].enum_items[af.current_connection_state.state].description,
			icon=connection_state_icons[af.current_connection_state.state])

		# Title
		provider_row = layout.row()
		text_column = provider_row.column()
		if af.current_provider_initialization.text.title != "":
			text_column.label(text=af.current_provider_initialization.text.title, icon="PLUGIN")
		else:
			text_column.label(text="(No title configured)", icon="PLUGIN")

		text_column.label(text=af.current_provider_initialization.text.description)

		# User data
		if af.current_connection_state.user.is_set:
			user_column = provider_row.column()
			if (af.current_connection_state.user.display_name != ""):
				user_column.label(text=af.current_connection_state.user.display_name, icon="USER")
			if (af.current_connection_state.user.display_tier != ""):
				user_column.label(text=af.current_connection_state.user.display_tier, icon="WORKSPACE")
			if (af.current_connection_state.unlock_balance.is_set):
				user_column.label(text=f"{af.current_connection_state.unlock_balance.balance} {af.current_connection_state.unlock_balance.balance_unit}", icon="RADIOBUT_ON")
