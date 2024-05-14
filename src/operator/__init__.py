import bpy
import bpy.utils.previews
from typing import Dict, List

from ..util.http import *
from .initialize_provider import *
from .connection_status import *
from .update_asset_list import *
from .build_import_plans import *
from .update_implementations_list import *
from .execute_import_plan import *
from .new_provider_bookmark import *
from .delete_provider_bookmark import *

# Registration and unregistration functions


def register():
	for cl in registration_targets:
		bpy.utils.register_class(cl)


def unregister():
	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)


registration_targets = [
	AF_OP_InitializeProvider, AF_OP_UpdateAssetList, AF_OP_UpdateImplementationsList, AF_OP_BuildImportPlans, AF_OP_ExecuteImportPlan, AF_OP_ConnectionStatus,
	AF_OP_NewProviderBookmark, AF_OP_DeleteProviderBookmark
]
