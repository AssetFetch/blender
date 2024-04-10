import logging
import bpy,os,shutil,tempfile,uuid

from ..property.datablocks import AF_PR_PreviewImageThumbnailBlock
from ..util import http
from ..ui import AF_PT_AssetPanel

LOGGER = logging.getLogger("af.ops.update_asset_list")
LOGGER.setLevel(logging.DEBUG)

class AF_OP_UpdateAssetList(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.update_asset_list"
	bl_label = "Update Asset List"
	bl_options = {"REGISTER","UNDO"}

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')
	
	@classmethod
	def poll(self, context) -> bool:
		af = bpy.context.window_manager.af
		return af.current_connection_state.state == "connected" and af.current_provider_initialization.asset_list_query.is_ready()

	def reset_thumbnails(self):
		"""Empties the temporary thumbnail directory and flushes all thumbnails from memory"""

		# Empty temp directory
		if os.path.exists(bpy.context.window_manager.af.thumbnail_directory):
			shutil.rmtree(bpy.context.window_manager.af.thumbnail_directory)
		os.makedirs(bpy.context.window_manager.af.thumbnail_directory,exist_ok=True)

		# Reset thumbnail data for all assets
		#for asset in bpy.context.window_manager.af.current_asset_list.assets:
		#	asset.preview_image_thumbnail.icon_id = -1

		# Clear icons from memory
		if AF_PT_AssetPanel.thumbnail_icons:
			AF_PT_AssetPanel.thumbnail_icons.clear()
		#AF_PT_AssetPanel.thumbnail_icons = bpy.utils.previews.new()

	def execute(self,context):
		af  = bpy.context.window_manager.af

		# Contact asset list endpoint
		response = af.current_provider_initialization.asset_list_query.to_http_query().execute()
		
		# Save assets in blender properties
		af.current_asset_list.configure(response.parsed)

		# Remove old thumbnails from disk and from blender's memory
		self.reset_thumbnails()

		return {'FINISHED'}
