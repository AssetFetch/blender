"""This module contains all operator classes for the addon."""

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
from .new_provider_bookmark_header import *
from .delete_provider_bookmark_header import *
from .asset_pagination import *


def register():
	"""Registers all operator classes.
	"""
	for cl in registration_targets:
		bpy.utils.register_class(cl)


def unregister():
	"""Unregisters all operator classes."""
	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)


# List of classes to be registered for the addon
registration_targets = [
	AF_OT_InitializeProvider, AF_OT_UpdateAssetList, AF_OT_UpdateImplementationsList, AF_OT_BuildImportPlans, AF_OT_ExecuteImportPlan, AF_OT_ConnectionStatus,
	AF_OT_NewProviderBookmark, AF_OT_DeleteProviderBookmark, AF_OT_DeleteProviderBookmarkHeader, AF_OT_NewProviderBookmarkHeader,
	AF_OT_SelectAsset, AF_OT_AssetPageFirst, AF_OT_AssetPagePrev, AF_OT_AssetPageNext, AF_OT_AssetPageLast,
]
