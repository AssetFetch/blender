import bpy
from ..property.preferences import *

class AF_OP_NewProviderBookmark(bpy.types.Operator):
	"""Creates a new provider bookmark."""

	bl_idname = "af.new_provider_bookmark"
	bl_label = "New Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):
		prefs = AF_PR_Preferences.get_prefs()
		prefs.provider_bookmarks.add()
		prefs.provider_bookmarks_index = len(prefs.provider_bookmarks) - 1
		return {'FINISHED'}