import logging
import os
import uuid
import bpy

from ..property.core import AF_PR_Asset
from ..util import http

LOGGER = logging.getLogger("af.ui.asset_panel")
LOGGER.setLevel(logging.DEBUG)

class AF_PT_AssetPanel(bpy.types.Panel):
	bl_label = "Assets"
	bl_idname = "AF_PT_ASSET_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	thumbnail_icons : bpy.utils.previews.ImagePreviewCollection = None

	@classmethod
	def poll(self, context) -> bool:
		af  = bpy.context.window_manager.af
		return af.current_connection_state.state == "connected"

	def load_thumbnail(self,asset : AF_PR_Asset):
		
		af  = bpy.context.window_manager.af
		preview_image_thumbnail = asset.preview_image_thumbnail
		
		LOGGER.debug(f"Loading thumbnail {preview_image_thumbnail.temp_file_id} for asset {asset.name}")

		thumb_file_location = os.path.join(af.thumbnail_directory,preview_image_thumbnail.temp_file_id)
		if not os.path.exists(thumb_file_location):
			# Thumbnail must be downloaded
			# Perform the file download into temp directory
			thumb_query = http.AF_HttpQuery(preview_image_thumbnail.get_optimal_resolution_uri(128),"get",None)
			thumb_query.execute_as_file(thumb_file_location)

		# Import the downloaded file
		if AF_PT_AssetPanel.thumbnail_icons is None:
			AF_PT_AssetPanel.thumbnail_icons = bpy.utils.previews.new()

		AF_PT_AssetPanel.thumbnail_icons.load(
			name=asset.name,
			path=thumb_file_location,
			path_type='IMAGE'
		)
		#asset.preview_image_thumbnail.icon_id = AF_PT_AssetPanel.thumbnail_icons[asset.name].icon_id

		LOGGER.debug(f"Loaded thumbnail into id {AF_PT_AssetPanel.thumbnail_icons[asset.name].icon_id}")

	def draw(self, context):
		layout = self.layout
		af  = bpy.context.window_manager.af

		# Query properties
		af.current_provider_initialization.asset_list_query.draw_ui(layout)

		# Send button
		#layout.operator("af.update_asset_list",text="Search Assets")
		
		if len(af.current_asset_list.assets) > 0:
			layout.separator()
			row = layout.row()
			row.template_list(listtype_name="UI_UL_list", list_id="asset_list", dataptr=af.current_asset_list, propname="assets", active_dataptr=af, active_propname="current_asset_list_index", maxrows=9)
			current_asset = af.current_asset_list.assets[af.current_asset_list_index]
			
			asset_box = row.box()
			asset_box.label(text=current_asset.text.title,icon="PACKAGE")

			if AF_PT_AssetPanel.thumbnail_icons is None or current_asset.name not in AF_PT_AssetPanel.thumbnail_icons:
				self.load_thumbnail(current_asset)
			#else:
			#	LOGGER.debug(f"Thumbnail is already present with id {AF_PT_AssetPanel.thumbnail_icons[current_asset.name].icon_id}")
		
			asset_box.template_icon(icon_value=AF_PT_AssetPanel.thumbnail_icons[current_asset.name].icon_id,scale=8.0)


		elif af.current_asset_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No assets found for this query.",icon="ORPHAN_DATA")
			
