import logging
import bpy,os,shutil,tempfile,uuid

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

	def execute(self,context):
		af  = bpy.context.window_manager.af

		# Contact asset list endpoint
		response = af.current_provider_initialization.asset_list_query.to_http_query().execute()
		
		# Save assets in blender properties
		af.current_asset_list.configure(response.parsed)

		return {'FINISHED'}
