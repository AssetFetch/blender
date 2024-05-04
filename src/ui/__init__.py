import bpy
from bpy.types import Context
from .provider_panel import *
from .asset_panel import *
from .implementations_panel import *
#from .import_steps_panel import *


def register():
	for cl in registration_targets:
		bpy.utils.register_class(cl)


def unregister():
	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)


registration_targets = [
    AF_PT_ProviderPanel,
    AF_PT_AssetPanel,
    AF_PT_ImplementationsPanel,
    #AF_PT_ImportStepsPanel
]
