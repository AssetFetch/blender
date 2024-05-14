import bpy
from .. import ADDON_NAME
from .templates import *

class AF_PR_ProviderBookmarkPref(bpy.types.PropertyGroup):
	init_url: bpy.props.StringProperty(default="(URI)",description="The initialization URL for this provider.",name="URI")
	header_values: bpy.props.CollectionProperty(type=AF_PR_GenericString)


from ..ui.preferences import draw_preferences
class AF_PR_Preferences(bpy.types.AddonPreferences):
	bl_idname = ADDON_NAME

	provider_bookmarks: bpy.props.CollectionProperty(type=AF_PR_ProviderBookmarkPref)
	provider_bookmarks_index: bpy.props.IntProperty(default=0)

	def draw(self, context):
		draw_preferences(self,context)

#def addon_preferences() -> AF_PR_Preferences:
#	return bpy.context.preferences.addons[ADDON_NAME].preferences