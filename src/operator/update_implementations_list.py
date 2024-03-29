import bpy


class AF_OP_UpdateImplementationsList(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.update_implementations_list"
	bl_label = "Update Implementations List"
	bl_options = {"REGISTER","UNDO"}

	#url: StringProperty(name="URL")

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):
		af  = bpy.context.window_manager.af
		current_asset = af.current_asset_list.assets[af.current_asset_list_index]

		# Contact implementations endpoint
		response = current_asset.implementation_list_query.to_http_query().execute()

		# Converting the json response into blender bpy data
		af['current_implementation_list'].clear()

		# Load the data into the implementation_list
		af.current_implementation_list.configure(response.parsed)

		# Update import plans
		bpy.ops.af.build_import_plans()

		return {'FINISHED'}