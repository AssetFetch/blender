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
	is_initialized: bpy.props.BoolProperty(default=False)

	def __init__(self) -> None:
		super().__init__()

	def draw(self, context):

		# TODO: This isn't the best place to put this!
		if not self.is_initialized:
			acg_bookmark = self.provider_bookmarks.add()
			acg_bookmark.name="ambientCG"
			acg_bookmark.init_url = "https://ambientcg.com/api/af/init"
			self.is_initialized = True
		from ..ui.preferences import draw_preferences
		draw_preferences(self,context)

def addon_preferences() -> AF_PR_Preferences:
	return bpy.context.preferences.addons[ADDON_NAME].preferences