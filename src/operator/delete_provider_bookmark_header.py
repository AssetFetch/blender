import bpy
from ..property.preferences import *

class AF_OP_DeleteProviderBookmarkHeader(bpy.types.Operator):
	"""Deletes the currently selected header from the provider bookmark."""

	bl_idname = "af.delete_provider_bookmark_header"
	bl_label = "Delete Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):
		prefs : AF_PR_Preferences = AF_PR_Preferences.get_prefs()
		current_bookmark = prefs.get_current_bookmark_in_preferences()
		current_bookmark.header_values.remove(prefs.provider_bookmarks_headers_index)
		prefs.provider_bookmarks_headers_index = max(0,prefs.provider_bookmarks_headers_index-1)
		return {'FINISHED'}