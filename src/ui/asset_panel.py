import logging
import bpy

from ..property.core import *
from ..util import http, ui_images
from ..operator.asset_pagination import PAGE_SIZE

LOGGER = logging.getLogger("af.ui.asset_panel")
LOGGER.setLevel(logging.DEBUG)


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

			# Pad remaining cells so the grid dimensions stay fixed on partial pages
			for _ in range(len(page_assets), PAGE_SIZE):
				cell = grid.column()
				cell.enabled = False
				cell_box = cell.box()
				cell_box.template_icon(icon_value=0, scale=4.0)
				cell_box.label(text="")

			# Pagination row: first, prev, centered label, next, last
			pag = layout.row(align=True)
			btn_first = pag.row(align=True)
			btn_first.enabled = (current_page_number > 0)
			btn_first.operator("af.asset_page_first", text="", icon="REW")
			btn_prev = pag.row(align=True)
			btn_prev.enabled = (current_page_number > 0)
			btn_prev.operator("af.asset_page_prev", text="", icon="TRIA_LEFT")
			lbl = pag.row(align=True)
			lbl.alignment = 'CENTER'
			lbl.label(text=f"Page {current_page_number + 1} / {total_page_count}")
			btn_next = pag.row(align=True)
			btn_next.enabled = (current_page_number < total_page_count - 1)
			btn_next.operator("af.asset_page_next", text="", icon="TRIA_RIGHT")
			btn_last = pag.row(align=True)
			btn_last.enabled = (current_page_number < total_page_count - 1)
			btn_last.operator("af.asset_page_last", text="", icon="FF")

		elif af.current_asset_list.already_queried:
			no_results_box = layout.box()
			no_results_box.label(text="No assets found for this query.", icon="ORPHAN_DATA")
