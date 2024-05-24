import bpy
from .. import ADDON_NAME
from .templates import *

class AF_PR_ProviderBookmarkPref(bpy.types.PropertyGroup):
	init_url: bpy.props.StringProperty(default="(URI)",description="The initialization URL for this provider.",name="URI")
	header_values: bpy.props.CollectionProperty(type=AF_PR_GenericString)


class AF_PR_Preferences(bpy.types.AddonPreferences):
	bl_idname = ADDON_NAME

	provider_bookmarks: bpy.props.CollectionProperty(type=AF_PR_ProviderBookmarkPref)
	provider_bookmarks_index: bpy.props.IntProperty(default=0)
	provider_bookmarks_headers_index: bpy.props.IntProperty(default=0)
	is_initialized: bpy.props.BoolProperty(default=False)

	def get_current_bookmark_in_preferences(self) -> AF_PR_ProviderBookmarkPref | None :
		return self.provider_bookmarks[self.provider_bookmarks_index]

	def draw(self, context):
		from ..ui.preferences import draw_preferences
		draw_preferences(self,context)

	@staticmethod
	def get_prefs():
		prefs = bpy.context.preferences.addons[ADDON_NAME].preferences
		if prefs:
			# TODO: This isn't the best place to put this!
			if not prefs.is_initialized:

				# ambientCG
				acg_bookmark = prefs.provider_bookmarks.add()
				acg_bookmark.name="ambientCG"
				acg_bookmark.init_url = "https://ambientcg.com/api/af/init"

				# Example
				example_bookmark = prefs.provider_bookmarks.add()
				example_bookmark.name="Advanced Python Example (see github.com/AssetFetch/examples)"
				example_bookmark.init_url = "http://localhost:8001"
				example_header = example_bookmark.header_values.add()
				example_header.name = "access-token"
				example_header.value = "debug"


				prefs.is_initialized = True
		return prefs