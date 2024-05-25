import bpy, logging
from ..util import http
from ..util.addon_constants import *

LOGGER = logging.getLogger("af.ops.connection_status")
LOGGER.setLevel(logging.DEBUG)


class AF_OP_ConnectionStatus(bpy.types.Operator):
	"""Performs a status query to the provider, if applicable."""

	bl_idname = "af.connection_status"
	bl_label = "Get Connection Status"
	bl_options = {"REGISTER", "INTERNAL"}

	@classmethod
	def poll(self, context) -> bool:
		"""Checks whether a connection status check can be performed with the current state."""
		af = bpy.context.window_manager.af

		# Check 1: Is a status query defined?
		if not af.current_provider_initialization.provider_configuration.connection_status_query.is_set:
			return False

		# Check 2: Are all required headers set?
		for h in af.current_provider_initialization.provider_configuration.headers:
			if h.is_required and h.value == "":
				return False

		return True

	def execute(self, context):
		af = bpy.context.window_manager.af

		try:
			# Start parsing with the assumption that the connection is OK
			af.current_connection_state.state = AF_ConnectionState.connected.value

			# Contact initialization endpoint and get the response from the provider
			LOGGER.info("Refreshing connection status.")
			query: http.AF_HttpQuery = af.current_provider_initialization.provider_configuration.connection_status_query.to_http_query()
			response: http.AF_HttpResponse = query.execute()

			# Set user data if available
			if "user" in response.parsed['data']:
				af.current_connection_state.user.configure(response.parsed['data']['user'])
			else:
				af.current_connection_state['user'].clear()

			# Set unlock balance if available
			if "unlock_balance" in response.parsed['data']:
				af.current_connection_state.unlock_balance.configure(response.parsed['data']['unlock_balance'])
			else:
				af.current_connection_state['unlock_balance'].clear()

			LOGGER.info("Refreshed connection status.")

		except Exception as e:
			af.current_connection_state.state = "connection_error"
			LOGGER.error(e)

		return {'FINISHED'}
