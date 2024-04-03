import bpy
from ..util import http
	
class AF_OP_ConnectionStatus(bpy.types.Operator):
	"""Performs a status query to the provider, if applicable."""

	bl_idname = "af.connection_status"
	bl_label = "Get Connection Status"
	bl_options = {"REGISTER"}

	@classmethod
	def poll(self,context):
		af = bpy.context.window_manager.af

		status_query_set = af.current_provider_initialization.provider_configuration.connection_status_query.is_set
		all_headers_set = True
		for h in af.current_provider_initialization.provider_configuration.headers:
			if h.value == "":
				all_headers_set = False

		return status_query_set and all_headers_set

	def execute(self,context):
		af = bpy.context.window_manager.af

		try:
			# Contact initialization endpoint and get the response
			response : http.AF_HttpResponse = af.current_provider_initialization.provider_configuration.connection_status_query.to_http_query().execute()

			af.current_connection_state.state = "connected"

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

		except Exception as e:
			af.current_connection_state.state = "connection_error"
			print(str(e))

		

		return {'FINISHED'}