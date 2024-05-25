import bpy
from ..property.templates import *
from ..property.preferences import *


class AF_UL_ProviderBookmarksItems(bpy.types.UIList):
	"""Class for rendering the list of bookmarks."""
	def draw_item(self, context, layout: bpy.types.UILayout, data, item: AF_PR_ProviderBookmark, icon, active_data, active_propname, index):
		if item.name != "":
			layout.label(text=item.name)
		else:
			row = layout.row()
			row.enabled = False
			row.label(text="(unnamed bookmark)")


class AF_UL_ProviderBookmarksHeadersItems(bpy.types.UIList):
	"""Class for rendering the list of headers for a bookmark."""
	def draw_item(self, context, layout: bpy.types.UILayout, data, item: AF_PR_GenericString, icon, active_data, active_propname, index):
		layout.prop(item, "name",text="Name")
		layout.prop(item, "value",text="Value")


def draw_preferences(self, context):
	"""Method for drawing the preferences UI in Blender's Preferences menu.
	This method gets called in the property/preferences module because preferences don't follow Blender's normal separation of
	Data and UI (It's all in one class)."""
	layout: bpy.types.UILayout = self.layout

	bookmarks = layout.column()
	bookmarks.label(text="Bookmarks")
	bookmarks_selection_row = bookmarks.row()
	bookmarks_selection_row.template_list(listtype_name="AF_UL_ProviderBookmarksItems",
		list_id="name",
		dataptr=self,
		propname="provider_bookmarks",
		active_dataptr=self,
		active_propname="provider_bookmarks_index",
		sort_lock=True,
		rows=3)

	bookmarks_selection_actions = bookmarks_selection_row.column(align=True)
	bookmarks_selection_actions.operator(operator="af.new_provider_bookmark", icon="ADD", text="")
	bookmarks_selection_actions.operator(operator="af.delete_provider_bookmark", icon="REMOVE", text="")

	bookmarks.separator()
	if len(self.provider_bookmarks) > 0:
		bookmarks.prop(self.provider_bookmarks[self.provider_bookmarks_index], "name")
		bookmarks.prop(self.provider_bookmarks[self.provider_bookmarks_index], "init_url")
		bookmarks.label(text="Credentials")
		bookmarks_header_config_row = bookmarks.row()
		bookmarks_header_config_row.template_list(listtype_name="AF_UL_ProviderBookmarksHeadersItems",
			list_id="name",
			dataptr=self.provider_bookmarks[self.provider_bookmarks_index],
			propname="header_values",
			active_dataptr=self,
			active_propname="provider_bookmarks_headers_index",
			sort_lock=True,
			rows=3)

		bookmarks_header_config_actions_col = bookmarks_header_config_row.column(align=True)
		bookmarks_header_config_actions_col.operator(operator="af.new_provider_bookmark_header", icon="ADD", text="")
		bookmarks_header_config_actions_col.operator(operator="af.delete_provider_bookmark_header", icon="REMOVE", text="")
	else:
		bookmarks.label(text="Add a bookmark to edit it here!")

	directories = layout.column()
	directories.label(text="Directories")
