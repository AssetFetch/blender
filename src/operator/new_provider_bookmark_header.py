import bpy
from ..property.preferences import *

class AF_OP_NewProviderBookmarkHeader(bpy.types.Operator):
	"""Adds a new header to the currently selected provider bookmark."""

	bl_idname = "af.new_provider_bookmark_header"
	bl_label = "New Header"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):
		prefs : AF_PR_Preferences = AF_PR_Preferences.get_prefs()
		current_bookmark = prefs.get_current_bookmark_in_preferences()
		current_bookmark.header_values.add()
		return {'FINISHED'}