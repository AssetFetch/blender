import bpy
from .http_handler import AF_HttpMethod

http_method_property = [
			('get','GET','HTTP GET'),
			('post','POST','HTTP POST')
		]

def register():

	# Import classes
	bpy.utils.register_class(AF_PR_Http_Header)
	bpy.utils.register_class(AF_PR_Http_Parameter)
	bpy.utils.register_class(AF_PR_Asset_Entry)
	bpy.utils.register_class(AF_PR_Implementation)

	# Initialization
	bpy.types.WindowManager.af_initialize_provider_url = bpy.props.StringProperty(default="http://localhost:8000")
	bpy.types.WindowManager.af_initialize_provider_title = bpy.props.StringProperty()
	bpy.types.WindowManager.af_initialize_provider_description = bpy.props.StringProperty()
	bpy.types.WindowManager.af_initialize_provider_headers = bpy.props.CollectionProperty(type=AF_PR_Http_Header)

	# Asset List
	bpy.types.WindowManager.af_asset_list_url = bpy.props.StringProperty()

	bpy.types.WindowManager.af_asset_list_method = bpy.props.EnumProperty(items=http_method_property)

	bpy.types.WindowManager.af_asset_list_parameters = bpy.props.CollectionProperty(type=AF_PR_Http_Parameter)
	bpy.types.WindowManager.af_asset_list_entries = bpy.props.CollectionProperty(type=AF_PR_Asset_Entry)
	bpy.types.WindowManager.af_asset_list_entries_index = bpy.props.IntProperty(default=-1)

	# Implementations List
	bpy.types.WindowManager.af_asset_implementations_options = bpy.props.CollectionProperty(type=AF_PR_Implementation)
	bpy.types.WindowManager.af_asset_implementations_options_index = bpy.props.IntProperty(default=-1)

def unregister():

	bpy.utils.unregister_class(AF_PR_Http_Header)
	bpy.utils.unregister_class(AF_PR_Http_Parameter)
	bpy.utils.unregister_class(AF_PR_Asset_Entry)
	bpy.utils.unregister_class(AF_PR_Implementation)


	del bpy.types.WindowManager.af_initialize_provider_url
	del bpy.types.WindowManager.af_initialize_provider_text
	del bpy.types.WindowManager.af_initialize_provider_headers

	del bpy.types.WindowManager.af_asset_list_url
	del bpy.types.WindowManager.af_asset_list_method
	del bpy.types.WindowManager.af_asset_list_parameters
	del bpy.types.WindowManager.af_asset_list_entries
	del bpy.types.WindowManager.af_asset_list_entries_index

class AF_PR_Implementation(bpy.types.PropertyGroup):
	#name -> id

	components_json: bpy.props.StringProperty


class AF_PR_Http_Header(bpy.types.PropertyGroup):
	#header_name: bpy.props.StringProperty(name="header_name",default="")
	value: bpy.props.StringProperty

class AF_PR_Http_Parameter(bpy.types.PropertyGroup):
	value: bpy.props.StringProperty
	type: bpy.props.StringProperty

class AF_PR_Asset_Entry(bpy.types.PropertyGroup):
	#name
	text_title: bpy.props.StringProperty
	text_description: bpy.props.StringProperty
	implementations_query_parameters: bpy.props.CollectionProperty(type=AF_PR_Http_Parameter)
	implementations_query_uri: bpy.props.StringProperty
	implementations_query_method: bpy.props.EnumProperty(items=http_method_property)