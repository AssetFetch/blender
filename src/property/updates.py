import bpy

def update_variable_query_parameter(property,context):
	if "update_target" in property:
		if property.update_target == "update_implementations_list":
			bpy.ops.af.update_implementations_list()
		if property.update_target == "update_asset_list":
			bpy.ops.af_update_asset_list()
	else:
		print(f"No update_target on {property}")


def update_assetfetch_asset_list_index(property,context):
	print("update_assetfetch_asset_list_index")
	bpy.context.window_manager.af['current_implementation_list'].clear()
	pass

def update_assetfetch_implementation_list_index(property,context):
	print("update_assetfetch_implementation_list_index")
	pass