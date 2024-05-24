import logging
import bpy

from ..property.templates import AF_VariableQueryUpdateTarget
from ..util import http
from ..property.preferences import *
from ..property.core import *

LOGGER = logging.getLogger("af.ops.initialize_provider")
LOGGER.setLevel(logging.DEBUG)


class AF_OP_InitializeProvider(bpy.types.Operator):
	"""Performs the initialization request to the provider."""

	bl_idname = "af.initialize_provider"
	bl_label = "Initialize Provider"
	bl_options = {"REGISTER", "INTERNAL"}

	def execute(self, context):

		af: AF_PR_AssetFetch = bpy.context.window_manager.af
		LOGGER.info(f"Initializing for {af.current_init_url}")

		# Reset existing connection_state
		if 'current_provider_initialization' in af:
			af['current_provider_initialization'].clear()

		if 'current_connection_state' in af:
			af['current_connection_state'].clear()

		if 'current_asset_list' in af:
			af['current_asset_list'].clear()

		if 'current_asset_list_index' in af:
			af['current_asset_list_index'] = 0

		if 'current_implementation_list' in af:
			af['current_implementation_list'].clear()

		if 'current_implementation_list_index' in af:
			af['current_implementation_list_index'] = 0

		try:
			# Contact initialization endpoint and get the response
			query = http.AF_HttpQuery(uri=af.current_init_url, method="get")
			response: http.AF_HttpResponse = query.execute()

			# Set the provider id
			if "id" in response.parsed:
				af.current_provider_initialization.name = response.parsed['id']
			else:
				raise Exception("No provider ID.")

			# Handle "text" datablock
			if "text" in response.parsed['data']:
				af.current_provider_initialization.text.configure(response.parsed['data']['text'])

			# Handle "provider_configuration" datablock
			af.current_provider_initialization.provider_configuration.headers.clear()
			if "provider_configuration" in response.parsed['data']:

				provider_config = response.parsed['data']['provider_configuration']

				# Test if the provider requests custom headers.
				if len(provider_config['headers']) > 0:
					af.current_connection_state.state = "awaiting_input"

					# Register headers
					for header_info in provider_config['headers']:
						current_header = af.current_provider_initialization.provider_configuration.headers.add()
						current_header.configure(header_info)

					# Populate header from preferences, if applicable
					if af['provider_bookmark_selection'] > 0:
						prefs = AF_PR_Preferences.get_prefs()
						bookmark = prefs.provider_bookmarks[af['provider_bookmark_selection'] - 1]
						for pref_header in bookmark.header_values:
							target_header = af.current_provider_initialization.provider_configuration.headers.get(pref_header.name)
							if target_header is not None:
								target_header.value = pref_header.value
				else:
					# If no headers are required, assume that the connection exists now.
					af.current_connection_state.state = "connected"

				# Configure the status endpoint
				af.current_provider_initialization.provider_configuration.connection_status_query.configure(provider_config['connection_status_query'])
			else:
				# No configuration required, we can immediately start getting the asset list (assuming the operator polling succeeded)
				af.current_connection_state.state = "connected"

			# Handle the asset list query description ("asset_list_query" datablock)
			if "asset_list_query" in response.parsed['data']:
				af.current_provider_initialization.asset_list_query.configure(response.parsed['data']['asset_list_query'],
					update_target=AF_VariableQueryUpdateTarget.update_asset_list_parameter)
				af.current_asset_list.already_queried = False
			else:
				raise Exception("No Asset List Query!")

			# Perform a connection status check, if the provider has offered an endpoint for it.
			if bpy.ops.af.connection_status.poll():
				LOGGER.debug("Getting connection status...")
				bpy.ops.af.connection_status()

		except Exception as e:
			af.current_connection_state.state = "connection_error"
			raise e

		return {'FINISHED'}
