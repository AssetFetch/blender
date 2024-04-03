import bpy

class AF_PT_AssetPanel(bpy.types.Panel):
	bl_label = "Assets"
	bl_idname = "AF_PT_ASSET_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	@classmethod
	def poll(self, context) -> bool:
		af  = bpy.context.window_manager.af
		return af.current_connection_state.state == "connected"

	def draw(self, context):
		layout = self.layout
		af  = bpy.context.window_manager.af

		# Query properties
		af.current_provider_initialization.asset_list_query.draw_ui(layout)

		# Send button
		#layout.operator("af.update_asset_list",text="Search Assets")

		# List of assets
			# Image
			# Title
			# (selectable)
		
		# Temporary icon test code:
		#icons_dict = bpy.utils.previews.new()
		#icons_dict.load("CAT_1","E:/Git/assetfetch-blender/tmp_icons/CAT_1.jpeg",'IMAGE')
		#layout.label(text="ASDF",icon_value=icons_dict['CAT_1'].icon_id)
		
		if len(af.current_asset_list.assets) > 0:
			layout.template_list(listtype_name="UI_UL_list", list_id="asset_list", dataptr=af.current_asset_list, propname="assets", active_dataptr=af, active_propname="current_asset_list_index")
			layout.separator()
			current_asset = af.current_asset_list.assets[af.current_asset_list_index]
			
			asset_box = layout.box()
			asset_box.label(text=current_asset.text.title,icon="PACKAGE")
			if current_asset.preview_image_thumbnail.icon_id:
				asset_box.template_icon(icon_value=current_asset.preview_image_thumbnail.icon_id,scale=8.0)
			else:
				asset_box.label(text="No thumbnail available.",icon="CANCEL")
		elif af.current_asset_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No assets found for this query.",icon="ORPHAN_DATA")
			
