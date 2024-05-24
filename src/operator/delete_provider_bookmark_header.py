import bpy
from ..property.preferences import *


class AF_OP_DeleteProviderBookmarkHeader(bpy.types.Operator):
	"""Deletes the currently selected header from the provider bookmark. Used in addon preferences."""

	bl_idname = "af.delete_provider_bookmark_header"
	bl_label = "Delete Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):

		# Get preferences
		prefs: AF_PR_Preferences = AF_PR_Preferences.get_prefs()

		# Load the currently selected bookmark
		current_bookmark = prefs.get_current_bookmark_in_preferences()

		# Remove the currently selected header entry from it
		current_bookmark.header_values.remove(prefs.provider_bookmarks_headers_index)
		prefs.provider_bookmarks_headers_index = max(0, prefs.provider_bookmarks_headers_index - 1)

		return {'FINISHED'}
