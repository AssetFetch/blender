import logging
import os
import uuid
import bpy

from ..property.core import *
from ..util import http, ui_images

LOGGER = logging.getLogger("af.ui.asset_panel")
LOGGER.setLevel(logging.DEBUG)


class AF_UL_AssetsItems(bpy.types.UIList):
	"""Renders each asset as a single-height row with a thumbnail icon and name."""

	def draw_item(self, context, layout: bpy.types.UILayout, data, item: AF_PR_Asset, icon, active_data, active_propname, index):
		thumbnail_uri = item.preview_image_thumbnail.get_optimal_resolution_uri(256)
		thumbnail_icon_id = ui_images.get_ui_image_icon_id(thumbnail_uri)
		layout.label(text=item.get_display_title(), icon_value=thumbnail_icon_id)
		print(f"Drawing asset {item.get_display_title()} with thumbnail {thumbnail_uri} and icon ID {thumbnail_icon_id}")


class AF_PT_AssetPanel(bpy.types.Panel):
	"""The asset selection panel."""

	bl_label = "Asset Selection"
	bl_idname = "AF_PT_ASSET_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'

	@classmethod
	def poll(self, context) -> bool:
		af = bpy.context.window_manager.af
		return af.current_connection_state.state == "connected"

	def draw(self, context):

		# Helpful variables
		layout = self.layout
		af = bpy.context.window_manager.af

		# Draw the form for the asset list query
		af.current_provider_initialization.asset_list_query.draw_ui(layout)

		# Test if there are assets to list
		if len(af.current_asset_list.assets) > 0:
			layout.separator()

			# Side-by-side: scrollable list on the left, large preview on the right.
			row = layout.row()

			row.template_list(listtype_name="AF_UL_AssetsItems",
				list_id="asset_list",
				dataptr=af.current_asset_list,
				propname="assets",
				active_dataptr=af,
				active_propname="current_asset_list_index",
				rows=7,
				maxrows=7)

			# Large preview column
			current_asset = af.current_asset_list.assets[af.current_asset_list_index]
			preview_col = row.column()
			preview_box = preview_col.box()
			preview_box.label(text=current_asset.get_display_title(), icon="ASSET_MANAGER")
			thumbnail_uri = current_asset.preview_image_thumbnail.get_optimal_resolution_uri(256)
			thumbnail_icon_id = ui_images.get_ui_image_icon_id(thumbnail_uri)
			preview_box.template_icon(icon_value=thumbnail_icon_id, scale=6.0)

		# Display a message if a query returned no results
		elif af.current_asset_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No assets found for this query.", icon="ORPHAN_DATA")
