import bpy
from ..property.preferences import *


class AF_OP_DeleteProviderBookmark(bpy.types.Operator):
	"""Deletes the currently selected provider bookmark."""

	bl_idname = "af.delete_provider_bookmark"
	bl_label = "Delete Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):

		# Get preferences
		prefs = AF_PR_Preferences.get_prefs()

		# Remove currently selected bookmark
		prefs.provider_bookmarks.remove(prefs.provider_bookmarks_index)
		prefs.provider_bookmarks_index = max(0, prefs.provider_bookmarks_index - 1)

		return {'FINISHED'}
