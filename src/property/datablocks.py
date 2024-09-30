"""This module contains blender bpy representations of all AssetFetch datablocks that are supported by the addon."""

import logging
import uuid
import bpy, re

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
	title: bpy.props.StringProperty()
	description: bpy.props.StringProperty()


class AF_PR_UserBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	display_name: bpy.props.StringProperty()
	display_tier: bpy.props.StringProperty()
	display_icon_uri: bpy.props.StringProperty()


class AF_PR_StoreBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):

	local_file_path: bpy.props.StringProperty()
	bytes: bpy.props.IntProperty()

	def configure(self, store):
		"""Custom configuration method for this datablock which validates that the file path does not make illegal relative references."""
		self.bytes = store['bytes']

		local_path: str = store['local_file_path']
		if local_path == "." or "./" in local_path or ".\\" in local_path:
			raise Exception("Local path contains an illegal reference (.)")
		if local_path == ".." or "../" in local_path or "..\\" in local_path:
			raise Exception("Local path contains an illegal reference (..)")

		self.local_file_path = local_path


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
	balance: bpy.props.FloatProperty()
	balance_unit: bpy.props.StringProperty()
	balance_refill_uri: bpy.props.StringProperty()


class AF_PR_ProviderReconfigurationBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	headers: bpy.props.CollectionProperty(type=AF_PR_GenericString)


class AF_PR_HandleNativeBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	pass


class AF_PR_FormatBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	extension: bpy.props.StringProperty()
	mediatype: bpy.props.StringProperty()

	def configure(self, format):
		self.extension = format['extension']
		if(format['mediatype']):
			self.mediatype = format['mediatype']


class AF_PR_HandleArchiveBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	extract_fully: bpy.props.BoolProperty()
	local_directory_path: bpy.props.StringProperty()

	def configure(self, handle_archive):

		self.extract_fully = handle_archive['extract_fully']

		path = handle_archive['local_directory_path']

		if path is not None:
			# Rule 1: It MUST end with a slash ("trailing slash")
			if not path.endswith('/'):
				raise Exception("Path must end with a slash ('/').")

			# Rule 2: It MUST NOT start with a slash (unless it's root '/')
			if path != '/' and path.startswith('/'):
				raise Exception("Path must not start with a slash unless it's the root ('/').")

			# Rule 3: It MUST not contain backslashes (\) as directory separators
			if '\\' in path:
				raise Exception("Path must not contain backslashes ('\\') as directory separators.")

			# Rule 4: It MUST NOT contain relative path references (./ or ../)
			if re.search(r'(^|/)\./|(^|/)\.\./', path):
				raise Exception("Path must not contain relative path references ('./' or '../').")

			self.local_directory_path = path


class AF_PR_FetchDownloadBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	unlock_query_id: bpy.props.StringProperty()
	download_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)

	def configure(self, fetch_download):
		self.download_query.configure(fetch_download['download_query'])

		# Maybe check if it exists?
		if (fetch_download['unlock_query_id']):
			self.unlock_query_id = fetch_download['unlock_query_id']
		else:
			self.unlock_query_id = ""


class AF_PR_FetchFromArchiveBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	archive_component_id: bpy.props.StringProperty()
	component_sub_path: bpy.props.StringProperty()


class AF_PR_HandleLooseEnvironmentBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	environment_name: bpy.props.StringProperty()
	projection: bpy.props.EnumProperty(items=[("equirectangular", "equirectangular", "equirectangular"), ("mirror_ball", "mirror_ball", "mirror_ball")])


class AF_PR_HandleLooseMaterialMapBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):
	material_name: bpy.props.StringProperty()
	map: bpy.props.EnumProperty(items=af_constants.AF_MaterialMap.property_items())


class AF_PR_LinkLooseMaterialBlock(bpy.types.PropertyGroup):
	material_name: bpy.props.StringProperty()


class AF_PR_FormatBlendTarget(bpy.types.PropertyGroup):
	names: bpy.props.CollectionProperty(type=AF_PR_GenericString)
	kind: bpy.props.EnumProperty(items=addon_constants.AF_BlenderDataTypes.property_items())


class AF_PR_FormatBlendBlock(bpy.types.PropertyGroup):

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


class AF_PR_FormatObjBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):

	up_axis: bpy.props.StringProperty()
	front_axis: bpy.props.StringProperty()

	blender_objects: bpy.props.CollectionProperty(type=AF_PR_GenericString)


class AF_PR_UnlockQuery(bpy.types.PropertyGroup):
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

	items: bpy.props.CollectionProperty(type=AF_PR_UnlockQuery)

	def configure(self, unlock_queries):
		for q in unlock_queries:
			self.items.add().configure(q)


class AF_PR_PreviewImageThumbnailBlock(bpy.types.PropertyGroup, AF_PR_GenericBlock):

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
