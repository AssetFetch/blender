"""This module contains blender bpy representations of all AssetFetch datablocks that are supported by the addon."""

import logging
import uuid
import bpy

from .updates import *
from .templates import *
from ..util import af_constants, addon_constants

LOGGER = logging.getLogger("af.property.datablocks")
LOGGER.setLevel(logging.DEBUG)


class AF_PR_GenericBlock:
	"""A class inheriting from AF_PR_GenericBlock means that its parameters
	can be loaded from a dict which is usually the result of parsed json.
	See https://stackoverflow.com/a/2466207 """

	# This property indicates whether the block should actually be treated as if it is present.
	# This is because in the blender data API every PointerProperty needs to be pre-allocated,
	# meaning that it would otherwise be impossible to tell which blocks are actually present.
	is_set: bpy.props.BoolProperty(default=False)

	def configure(self, initial_data):
		"""Configures this datablock using a dict that is the result of parsing the JSON from the provider."""
		for key in initial_data.keys():
			try:
				setattr(self, key, initial_data[key])
			except Exception as e:
				LOGGER.warn(f"skipping {key} because {e}")
		self.is_set = True


class AF_PR_TextBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#841-text"""
	title: bpy.props.StringProperty()
	description: bpy.props.StringProperty()


class AF_PR_UserBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#813-user"""
	display_name: bpy.props.StringProperty()
	display_tier: bpy.props.StringProperty()
	display_icon_uri: bpy.props.StringProperty()


class AF_PR_FileInfoBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#831-file_info"""
	length: bpy.props.IntProperty()
	extension: bpy.props.StringProperty()


class AF_PR_FileHandleBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#832-file_handle"""
	local_path: bpy.props.StringProperty()
	behavior: bpy.props.EnumProperty(items=[('single_active', 'single_active', 'single_active'), ('single_passive', 'single_passive',
		'single_passive'), ('archive_unpack_fully', 'archive_unpack_fully',
		'archive_unpack_fully'), ('archive_unpack_referenced', 'archive_unpack_referenced', 'archive_unpack_referenced')])

	def configure(self, file_handle):
		"""Custom configuration method for this datablock which validates that the file path does not make illegal relative references."""
		self.behavior = file_handle['behavior']

		local_path: str = file_handle['local_path']
		if local_path == "." or "./" in local_path or ".\\" in local_path:
			raise Exception("Local path contains an illegal reference (.)")
		if local_path == ".." or "../" in local_path or "..\\" in local_path:
			raise Exception("Local path contains an illegal reference (..)")
		self.local_path = local_path


class AF_PR_Header(bpy.types.PropertyGroup):
	""""""

	default: bpy.props.StringProperty()
	is_required: bpy.props.BoolProperty()
	is_sensitive: bpy.props.BoolProperty()
	prefix: bpy.props.StringProperty()
	suffix: bpy.props.StringProperty()
	title: bpy.props.StringProperty()
	encoding: bpy.props.EnumProperty(items=[("plain", "plain", "plain"), ("base64", "base64", "base64")])

	# The actual value entered by the user
	value: bpy.props.StringProperty(update=update_provider_header)

	def configure(self, header):
		for key in ['name', 'default', 'is_required', 'is_sensitive', 'prefix', 'suffix', 'title', 'encoding']:
			if key in header:
				setattr(self, key, header[key])
		self.value = self.default


class AF_PR_ProviderConfigurationBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#811-provider_configuration"""
	headers: bpy.props.CollectionProperty(type=AF_PR_Header)
	connection_status_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)
	header_acquisition_uri: bpy.props.StringProperty()
	header_acquisition_uri_title: bpy.props.StringProperty()

	def configure(self, provider_configuration):
		for h in provider_configuration['headers']:
			self.headers.add().configure(h)
		self.connection_status_query.configure(provider_configuration['connection_status_query'])
		self.header_acquisition_uri = provider_configuration['header_acquisition_uri']
		self.header_acquisition_uri_title = provider_configuration['header_acquisition_uri_title']

		self.is_set = True


class AF_PR_UnlockBalanceBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#871-unlock_balance"""
	balance: bpy.props.FloatProperty()
	balance_unit: bpy.props.StringProperty()
	balance_refill_uri: bpy.props.StringProperty()


class AF_PR_ProviderReconfigurationBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#812-provider_reconfiguration"""
	headers: bpy.props.CollectionProperty(type=AF_PR_GenericString)


class AF_PR_FileFetchFromArchiveBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#835-file_fetchfrom_archive"""
	archive_component_id: bpy.props.StringProperty()
	component_path: bpy.props.StringProperty()


class AF_PR_FileFetchDownloadPostUnlockBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#834-file_fetchdownload_post_unlock"""
	unlock_query_id: bpy.props.StringProperty()
	unlocked_data_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)

	def configure(self, file_fetch_download_post_unlock):
		self.unlock_query_id = file_fetch_download_post_unlock['unlock_query_id']
		self.unlocked_data_query.configure(file_fetch_download_post_unlock['unlocked_data_query'])


class AF_PR_LooseEnvironmentBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#851-loose_environment"""
	projection: bpy.props.EnumProperty(items=[("equirectangular", "equirectangular", "equirectangular"), ("mirror_ball", "mirror_ball", "mirror_ball")])


class AF_PR_LooseMaterialDefineBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#852-loose_materialdefine"""
	material_name: bpy.props.StringProperty()
	map: bpy.props.EnumProperty(items=af_constants.AF_MaterialMap.property_items())
	colorspace: bpy.props.EnumProperty(items=af_constants.AF_Colorspace.property_items())


class AF_PR_LooseMaterialApplyElement(bpy.types.PropertyGroup):
	material_name: bpy.props.StringProperty()
	apply_selectively_to: bpy.props.StringProperty()


class AF_PR_LooseMaterialApplyBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#853-loose_materialapply"""
	items: bpy.props.CollectionProperty(type=AF_PR_LooseMaterialApplyElement)

	def configure(self, loose_material_apply):
		for elem in loose_material_apply:
			new_item = self.items.add()
			new_item.material_name = elem['material_name']
			if "apply_selectively_to" in elem and elem['apply_selectively_to'] != None:
				new_item.apply_selectively_to = elem['apply_selectively_to']


class AF_PR_FormatBlendTarget(bpy.types.PropertyGroup):
	names: bpy.props.CollectionProperty(type=AF_PR_GenericString)
	kind: bpy.props.EnumProperty(items=addon_constants.AF_BlenderDataTypes.property_items())


class AF_PR_FormatBlendBlock(bpy.types.PropertyGroup):
	"""https://assetfetch.org/spec/0.3/#861-formatblend"""
	version: bpy.props.StringProperty()
	is_asset: bpy.props.BoolProperty()
	targets: bpy.props.CollectionProperty(type=AF_PR_FormatBlendTarget)

	# The complex target object means that we need a custom config method
	def configure(self, format_blend):
		self.version = format_blend['version']
		self.is_asset = format_blend['is_asset']
		for t in format_blend['targets']:
			new_target = self.targets.add()
			new_target.kind = t['kind']
			for n in t['names']:
				new_name = new_target.names.add()
				new_name.value = n


class AF_PR_FormatUsdBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#862-formatusd"""
	is_crate: bpy.props.BoolProperty()


class AF_PR_FormatObjBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#863-formatobj"""
	up_axis: bpy.props.StringProperty()

	blender_objects: bpy.props.CollectionProperty(type=AF_PR_GenericString)


class AF_PR_UnlockQuery(bpy.types.PropertyGroup):
	"""Single element of the unlock_queries list"""

	unlocked: bpy.props.BoolProperty(default=False)
	price: bpy.props.FloatProperty()
	unlock_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)
	unlock_query_fallback_uri: bpy.props.StringProperty()

	def configure(self, unlock_query):
		self.name = unlock_query['id']
		if "unlocked" in unlock_query:
			self.unlocked = unlock_query['unlocked']
		if "price" in unlock_query:
			self.price = unlock_query['price']
		if "unlock_query" in unlock_query:
			self.unlock_query.configure(unlock_query['unlock_query'])
		if "unlock_query_fallback_uri" in unlock_query and unlock_query['unlock_query_fallback_uri']:
			self.unlock_query_fallback_uri = unlock_query['unlock_query_fallback_uri']


class AF_PR_UnlockQueriesBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#872-unlock_queries"""
	items: bpy.props.CollectionProperty(type=AF_PR_UnlockQuery)

	def configure(self, unlock_queries):
		for q in unlock_queries:
			self.items.add().configure(q)


class AF_PR_PreviewImageThumbnailBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	"""https://assetfetch.org/spec/0.3/#849-preview_image_thumbnail"""
	alt: bpy.props.StringProperty()
	uris: bpy.props.CollectionProperty(type=AF_PR_GenericString)

	def configure(self, preview_image_thumbnail):
		self.is_set = True
		if "alt" in preview_image_thumbnail:
			self.alt = preview_image_thumbnail['alt']
		for resolution in preview_image_thumbnail['uris'].keys():
			new_res = self.uris.add()
			new_res.name = resolution
			new_res.value = preview_image_thumbnail['uris'][resolution]

	def get_optimal_resolution_uri(self, target_resolution: int) -> str:
		"""Finds the best available thumbnail image for a given target resolution."""

		current_optimal_resolution = None

		for res in self.uris.keys():

			res = int(res)

			if (current_optimal_resolution is None):
				current_optimal_resolution = res

			if (res > 0 and current_optimal_resolution == 0):
				current_optimal_resolution = res

			if (res > 0 and abs(current_optimal_resolution - target_resolution) > abs(res - target_resolution)):
				current_optimal_resolution = res

		final_uri = self.uris[str(current_optimal_resolution)]
		return final_uri
