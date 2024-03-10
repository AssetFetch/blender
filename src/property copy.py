import bpy
from .http_handler import AF_HttpMethod

http_method_enum = [
			('get','GET','HTTP GET'),
			('post','POST','HTTP POST')
		]

def register():

	# Import classes
	bpy.utils.register_class(AF_PR_Http_Header)
	bpy.utils.register_class(AF_PR_Http_Parameter)
	bpy.utils.register_class(AF_PR_Asset_Entry)
	bpy.utils.register_class(AF_PR_Implementation)
	bpy.utils.register_class(AF_PR_Response)
	bpy.utils.register_class(AF_PR_Initialization_Response)
	bpy.utils.register_class(AF_PR_Asset_List_Response)

	# Register AF property group
	bpy.types.WindowManager.af_init = bpy.props.PointerProperty(type=AF_PR_Initialization_Response)

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
	del bpy.types.WindowManager.af_initialize_provider_title
	del bpy.types.WindowManager.af_initialize_provider_headers

	del bpy.types.WindowManager.af_asset_list_url
	del bpy.types.WindowManager.af_asset_list_method
	del bpy.types.WindowManager.af_asset_list_parameters
	del bpy.types.WindowManager.af_asset_list_entries
	del bpy.types.WindowManager.af_asset_list_entries_index

# Templates
	
class AF_PR_Fixed_Query(bpy.types.PropertyGroup):
	uri: bpy.props.StringProperty
	method: bpy.props.EnumProperty(items=http_method_enum)
	payload: bpy.props.CollectionProperty(types=bpy.props.StringProperty)

class AF_PR_Response_Meta_Data(bpy.types.PropertyGroup):
	http_status: bpy.props.IntProperty
	message: bpy.props.StringProperty

# Datablocks

class AF_PR_DB_Text:
	title: bpy.types.StringProperty
	description: bpy.types.StringProperty

# Rest

class AF_PR_InitializationData(bpy.types.PropertyGroup):
	asset_list_query : bpy.props.PointerProperty(type=AF_PR_Fixed_Query)
	data_text : bpy.props.PointerProperty(type=AF_PR_DB_Text)
	data_asset_list_query:

class AF_PR_AssetFetch(bpy.types.PropertyGroup):
	last_response_meta: bpy.props.PointerProperty(type=AF_PR_Response_Meta_Data)
	initialization: bpy.props.PointerProperty(type=AF_PR_Initialization_Data)

"""
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

class AF_PR_Response(bpy.types.PropertyGroup):
	http_code = bpy.props.IntProperty
	message = bpy.props.StringProperty
	kind = bpy.props.EnumProperty(items=[
			('initialization','Initialization Endpoint','Response data from initialization endpoint'),
			('asset_list','Asset List Endpoint','Response date from the asset_list endpoint')
		])

class AF_PR_Initialization_Response(AF_PR_Response):
	data: bpy.props.StringProperty 

class AF_PR_Asset_List_Response(AF_PR_Response):
	data: bpy.props.CollectionProperty(type=AF_PR_Datablock)
"""