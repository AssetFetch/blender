import os, sys, logging

print("Loading AssetFetch for Blender v0.1.0")
logging.basicConfig()
logging.root.setLevel(logging.WARN)

# Add the lib/ directory to sys.path to make it all the bundled libraries importable
LIB_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
if LIB_PATH not in sys.path:
	sys.path.insert(0, LIB_PATH)

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           "json-schema")

bl_info = {
    "name": "assetfetch-blender",
    "description": "AssetFetch for Blender",
    "author": "ambientCG / Lennart Demes",
    "version": (0, 1),
    "blender": (4, 0, 0),
    "location": "View3D",
    "category": "3D View"
}


def register():

	from .property import register
	property.register()

	from .operator import register
	operator.register()

	from .ui import register
	ui.register()

	from .util.ui_images import reset_image_cache
	reset_image_cache()


def unregister():

	from .util.ui_images import reset_image_cache
	reset_image_cache()

	from .ui import unregister
	ui.unregister()

	from .operator import unregister
	operator.unregister()

	from .property import unregister
	property.unregister()
