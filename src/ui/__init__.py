import bpy
from bpy.types import Context
from .provider_panel import *
from .asset_panel import *
from .implementations_panel import *
from .preferences import *


def register():
	for cl in registration_targets:
		bpy.utils.register_class(cl)


def unregister():
	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)


registration_targets = [
	AF_PT_ProviderPanel,
	AF_UL_AssetsItems,
	AF_PT_AssetPanel,
	AF_UL_ImplementationsItems,
	AF_PT_ImplementationsPanel,
	AF_UL_ProviderBookmarksItems,
	AF_UL_ProviderBookmarksHeadersItems
	#AF_PT_ImportStepsPanel
]
