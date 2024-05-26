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
		layout.prop(item, "name", text="Key")
		layout.prop(item, "value", text="Value")


class AF_UL_LocalDirectoryRulesItem(bpy.types.UIList):
	"""Class for rendering the list of local directory rules."""

	def draw_item(self, context, layout: bpy.types.UILayout, data, item: AF_PR_LocalDirectoryRule, icon, active_data, active_propname, index):
		layout.prop(item, "blend_directory")


#def draw_preferences(self, context):
def draw_preferences(prefs, layout: bpy.types.UILayout, context):
	"""Method for drawing the preferences UI in Blender's Preferences menu.
	This method gets called in the property/preferences module because preferences don't follow Blender's normal separation of
	Data and UI (It's all in one class)."""

	pref_tabs = layout.row()
	pref_tabs.prop(prefs, "display_mode", expand=True)

	# Bookmark List
	if prefs.display_mode == "bookmarks":
		bookmarks = layout.column()
		bookmarks_selection_row = bookmarks.row()
		bookmarks_selection_row.template_list(listtype_name="AF_UL_ProviderBookmarksItems",
			list_id="name",
			dataptr=prefs,
			propname="provider_bookmarks",
			active_dataptr=prefs,
			active_propname="provider_bookmarks_index",
			sort_lock=True,
			rows=3)

		bookmarks_selection_actions = bookmarks_selection_row.column(align=True)
		bookmarks_selection_actions.operator(operator="af.new_provider_bookmark", icon="ADD", text="")
		bookmarks_selection_actions.operator(operator="af.delete_provider_bookmark", icon="REMOVE", text="")

		# Bookmark Configuration
		if len(prefs.provider_bookmarks) > 0:
			bookmarks.prop(prefs.provider_bookmarks[prefs.provider_bookmarks_index], "name")
			bookmarks.prop(prefs.provider_bookmarks[prefs.provider_bookmarks_index], "init_url")
			bookmarks.label(text="Credentials")
			bookmarks_header_config_row = bookmarks.row()
			bookmarks_header_config_row.template_list(listtype_name="AF_UL_ProviderBookmarksHeadersItems",
				list_id="name",
				dataptr=prefs.provider_bookmarks[prefs.provider_bookmarks_index],
				propname="header_values",
				active_dataptr=prefs,
				active_propname="provider_bookmarks_headers_index",
				sort_lock=True,
				rows=3)

			bookmarks_header_config_actions_col = bookmarks_header_config_row.column(align=True)
			bookmarks_header_config_actions_col.operator(operator="af.new_provider_bookmark_header", icon="ADD", text="")
			bookmarks_header_config_actions_col.operator(operator="af.delete_provider_bookmark_header", icon="REMOVE", text="")
		else:
			bookmarks.label(text="Add a bookmark to edit it here!")

	# Directory Configuration

	if prefs.display_mode == "directory":

		# Rules
		directories = layout.column()

		directories_rules = directories.box()
		directories_rules.prop(prefs, "use_rules", text="Use rule-based download directories")

		directories_rules_config = directories_rules.row()
		directories_rules_config.template_list(listtype_name="AF_UL_LocalDirectoryRulesItem",
			list_id="name",
			dataptr=prefs,
			propname="directory_rules",
			active_dataptr=prefs,
			active_propname="directory_rules_index",
			sort_lock=True,
			rows=3)

		directories_rules_actions = directories_rules_config.column(align=True)
		directories_rules_actions.operator(operator="af.new_directory_rule", icon="ADD", text="")
		directories_rules_actions.operator(operator="af.delete_directory_rule", icon="REMOVE", text="")

		directories_rules_config.enabled = prefs.use_rules

		# Relative
		directories_relative = directories.box()
		directories_relative.prop(prefs, "use_relative", text="Use download directory relative to currently opened file")
		directories_relative_config = directories_relative.column()
		directories_relative_config.prop(prefs, "relative_directory", text="Relative Path")

		directories_relative_config.enabled = prefs.use_relative

		# Absolute/Fallback
		directories_default = directories.box()
		directories_default.label(text="Default download directory", icon="FILE_FOLDER")
		directories_default.prop(prefs, "default_directory", text="Path")


class AF_PT_Preferences(bpy.types.Panel):
	"""Class for rendering the preferences in the main GUI, instead of only in blender's prefs menu."""

	bl_label = "Preferences"
	bl_idname = "AF_PT_Preferences_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'AssetFetch'
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		draw_preferences(AF_PR_Preferences.get_prefs(), self.layout, context)
