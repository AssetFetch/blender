import bpy

class AF_OP_NewProviderBookmark(bpy.types.Operator):
	"""Creates a new provider bookmark."""

	bl_idname = "af.new_provider_bookmark"
	bl_label = "New Bookmark"
	bl_options = {"REGISTER", "INTERNAL"}