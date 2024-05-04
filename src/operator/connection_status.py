import bpy, logging
from ..util import http

LOGGER = logging.getLogger("af.ops.connection_status")
LOGGER.setLevel(logging.DEBUG)


class AF_OP_ConnectionStatus(bpy.types.Operator):
	"""Performs a status query to the provider, if applicable."""

	bl_idname = "af.connection_status"
	bl_label = "Get Connection Status"
	bl_options = {"REGISTER", "INTERNAL"}

	@classmethod
	def poll(self, context):
		af = bpy.context.window_manager.af

		status_query_set = af.current_provider_initialization.provider_configuration.connection_status_query.is_set
		all_headers_set = True
		for h in af.current_provider_initialization.provider_configuration.headers:
			if h.value == "":
				all_headers_set = False

		return status_query_set and all_headers_set

	def execute(self, context):
		af = bpy.context.window_manager.af

		try:
			# Contact initialization endpoint and get the response
			LOGGER.info("Refreshing connection status.")
			response: http.AF_HttpResponse = af.current_provider_initialization.provider_configuration.connection_status_query.to_http_query(
			).execute()

			af.current_connection_state.state = "connected"

			# Set user data if available
			if "user" in response.parsed['data']:
				af.current_connection_state.user.configure(
				    response.parsed['data']['user'])
			else:
				af.current_connection_state['user'].clear()

			# Set unlock balance if available
			if "unlock_balance" in response.parsed['data']:
				af.current_connection_state.unlock_balance.configure(
				    response.parsed['data']['unlock_balance'])
			else:
				af.current_connection_state['unlock_balance'].clear()

			LOGGER.info("Refreshed connection status.")

		except Exception as e:
			af.current_connection_state.state = "connection_error"
			LOGGER.error(e)

		return {'FINISHED'}
