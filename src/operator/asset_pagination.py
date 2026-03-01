import logging
import bpy

LOGGER = logging.getLogger("af.operator.asset_pagination")
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


class AF_OT_AssetPageFirst(bpy.types.Operator):
	"""Jump to the first page of assets."""

	bl_idname = "af.asset_page_first"
	bl_label = "First Page"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		bpy.context.window_manager.af.current_asset_page_index = 0
		return {'FINISHED'}


class AF_OT_AssetPageLast(bpy.types.Operator):
	"""Jump to the last page of assets."""

	bl_idname = "af.asset_page_last"
	bl_label = "Last Page"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		af = bpy.context.window_manager.af
		total = len(af.current_asset_list.assets)
		af.current_asset_page_index = max(0, (total + PAGE_SIZE - 1) // PAGE_SIZE - 1)
		return {'FINISHED'}
