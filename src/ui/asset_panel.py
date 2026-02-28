import logging
import bpy

from ..property.core import *
from ..util import http, ui_images

LOGGER = logging.getLogger("af.ui.asset_panel")
LOGGER.setLevel(logging.DEBUG)

PAGE_SIZE = 12


class AF_OT_SelectAsset(bpy.types.Operator):
	"""Select an asset by index."""

	bl_idname = "af.select_asset"
	bl_label = "Select Asset"
	bl_options = {'INTERNAL'}

	index: bpy.props.IntProperty()

	def execute(self, context):
		bpy.context.window_manager.af.current_asset_list_index = self.index
		return {'FINISHED'}


class AF_OT_AssetPageNext(bpy.types.Operator):
	"""Advance to the next page of assets."""

	bl_idname = "af.asset_page_next"
	bl_label = "Next Page"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		af = bpy.context.window_manager.af
		total = len(af.current_asset_list.assets)
		total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
		if af.current_asset_page_index < total_pages - 1:
			af.current_asset_page_index += 1
		return {'FINISHED'}


class AF_OT_AssetPagePrev(bpy.types.Operator):
	"""Go back to the previous page of assets."""

	bl_idname = "af.asset_page_prev"
	bl_label = "Previous Page"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		af = bpy.context.window_manager.af
		if af.current_asset_page_index > 0:
			af.current_asset_page_index -= 1
		return {'FINISHED'}


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

		layout = self.layout
		af = bpy.context.window_manager.af

		# Draw the form for the asset list query
		af.current_provider_initialization.asset_list_query.draw_ui(layout)

		if len(af.current_asset_list.assets) > 0:
			layout.separator()

			total_asset_count = len(af.current_asset_list.assets)
			total_page_count = max(1, (total_asset_count + PAGE_SIZE - 1) // PAGE_SIZE)

			current_page_number = min(af.current_asset_page_index, total_page_count - 1)
			page_start_index = current_page_number * PAGE_SIZE
			page_assets = list(af.current_asset_list.assets)[page_start_index:page_start_index + PAGE_SIZE]

			# 3-column thumbnail grid
			grid = layout.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
			for i, asset in enumerate(page_assets):
				global_index = page_start_index + i
				is_selected = (global_index == af.current_asset_list_index)
				cell = grid.column()
				cell.alignment = 'CENTER'
				# Always box every cell so all cells stay the same size
				cell_box = cell.box()
				thumbnail_uri = asset.preview_image_thumbnail.get_optimal_resolution_uri(128)
				thumbnail_icon_id = ui_images.get_ui_image_icon_id(thumbnail_uri)
				cell_box.template_icon(icon_value=thumbnail_icon_id, scale=4.0)
				# Always embossed so the button outline makes it clear it's clickable
				icon = 'CHECKBOX_HLT' if is_selected else 'CHECKBOX_DEHLT'
				op = cell_box.operator("af.select_asset", text=asset.get_display_title(), emboss=True, icon=icon)
				op.index = global_index

			# Pagination row
			pag = layout.row(align=True)
			pag.operator("af.asset_page_prev", text="", icon="TRIA_LEFT")
			pag.label(text=f"Page {current_page_number + 1} / {total_page_count}")
			pag.operator("af.asset_page_next", text="", icon="TRIA_RIGHT")

		elif af.current_asset_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No assets found for this query.", icon="ORPHAN_DATA")
