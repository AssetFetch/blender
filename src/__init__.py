"""This is the main module of the "AssetFetch For Blender" addon.
It houses the main register() and unregister() functions for the addon along with required metadata.
"""

import os, sys
import bpy

print("Loading AssetFetch for Blender 0.4.0")

ADDON_NAME = __package__


def register():
	"""The main registration function for the entire addon.
	It calls the other registration functions to load all modules.
	"""
	from .property import register
	property.register()

	from .operator import register
	operator.register()

	from .ui import register
	ui.register()

	from .util.ui_images import reset_image_cache
	reset_image_cache()


def unregister():
	"""Main unregistration function for the entire addon (used during uninstallation)."""

	from .util.ui_images import reset_image_cache
	reset_image_cache()

	from .ui import unregister
	ui.unregister()

	from .operator import unregister
	operator.unregister()

	from .property import unregister
	property.unregister()
