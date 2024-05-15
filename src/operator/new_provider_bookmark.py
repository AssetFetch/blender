import bpy
from ..property.preferences import addon_preferences

class AF_OP_NewProviderBookmark(bpy.types.Operator):
	"""Creates a new provider bookmark."""

	bl_idname = "af.new_provider_bookmark"
	bl_label = "New Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):
		addon_preferences().provider_bookmarks.add()
		addon_preferences().provider_bookmarks_index = len(addon_preferences().provider_bookmarks) - 1
		return {'FINISHED'}