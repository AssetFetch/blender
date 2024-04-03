from enum import Enum
import bpy

class AF_VariableQueryUpdateTarget(Enum):
	update_asset_list_parameter = "update_asset_list_parameter"
	update_implementation_list_parameter = "update_implementation_list_parameter"
	update_nothing = "update_nothing"

	@classmethod
	def to_property_enum(cls):
		return list(map(lambda c: (c.value,c.value,c.value), cls))

def update_asset_list_index(property,context):
	print("update_asset_list_index")
	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()

def update_implementation_list_index(property,context):
	print("update_implementation_list_index")

def update_asset_list_parameter(property,context):
	print("update_asset_list_parameter")
	if bpy.ops.af.update_asset_list.poll():
		bpy.ops.af.update_asset_list()
	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()

def update_implementation_list_parameter(property,context):
	print("update_implementation_list_parameter")
	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()

def update_variable_query_parameter(property,context):
	print("update_variable_query_parameter")
	if hasattr(property,"update_target"):
		if property.update_target == AF_VariableQueryUpdateTarget.update_implementation_list_parameter.value:
			update_implementation_list_parameter(property,context)
		if property.update_target == AF_VariableQueryUpdateTarget.update_asset_list_parameter.value:
			update_asset_list_parameter(property,context)
	else:
		print(f"No update_target on {property}")