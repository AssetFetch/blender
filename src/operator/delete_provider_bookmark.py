import bpy
from ..property.preferences import addon_preferences

class AF_OP_DeleteProviderBookmark(bpy.types.Operator):
	"""Creates a new provider bookmark."""

	bl_idname = "af.delete_provider_bookmark"
	bl_label = "Delete Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):
		addon_preferences().provider_bookmarks.remove(addon_preferences().provider_bookmarks_index)
		addon_preferences().provider_bookmarks_index = max(0,addon_preferences().provider_bookmarks_index-1)
		return {'FINISHED'}