import bpy

class AF_OP_DeleteProviderBookmark(bpy.types.Operator):
	"""Creates a new provider bookmark."""

	bl_idname = "af.delete_provider_bookmark"
	bl_label = "Delete Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}