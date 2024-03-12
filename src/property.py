import bpy
from .http_handler import AF_HttpMethod
import sys,inspect

http_method_enum = [
			('get','GET','HTTP GET'),
			('post','POST','HTTP POST')
		]

def register():

	# Import classes
	bpy.utils.register_class(AF_PR_Generic_String)
	bpy.utils.register_class(AF_PR_Fixed_Query)
	bpy.utils.register_class(AF_PR_Parameter)
	bpy.utils.register_class(AF_PR_Variable_Query)

	bpy.utils.register_class(AF_PR_DB_Text)
	bpy.utils.register_class(AF_PR_DB_User)
	bpy.utils.register_class(AF_PR_DB_File_Info)

	bpy.utils.register_class(AF_PR_Header)
	bpy.utils.register_class(AF_PR_Provider_Initialization)
	bpy.utils.register_class(AF_PR_Asset)	
	bpy.utils.register_class(AF_PR_Asset_List)	
	bpy.utils.register_class(AF_PR_Component)	
	bpy.utils.register_class(AF_PR_Implementation)	
	bpy.utils.register_class(AF_PR_Implementation_List)	
	bpy.utils.register_class(AF_PR_AssetFetch)	


	bpy.types.WindowManager.af = bpy.props.PointerProperty(type=AF_PR_AssetFetch)

def unregister():

	bpy.utils.unregister_class(AF_PR_Generic_String)
	bpy.utils.unregister_class(AF_PR_Fixed_Query)
	bpy.utils.unregister_class(AF_PR_Parameter)
	bpy.utils.unregister_class(AF_PR_Variable_Query)
	
	bpy.utils.unregister_class(AF_PR_DB_Text)
	bpy.utils.unregister_class(AF_PR_DB_User)
	bpy.utils.unregister_class(AF_PR_DB_File_Info)

	bpy.utils.unregister_class(AF_PR_Header)
	bpy.utils.unregister_class(AF_PR_Provider_Initialization)
	bpy.utils.unregister_class(AF_PR_Asset)	
	bpy.utils.unregister_class(AF_PR_Asset_List)	
	bpy.utils.unregister_class(AF_PR_Component)	
	bpy.utils.unregister_class(AF_PR_Implementation)	
	bpy.utils.unregister_class(AF_PR_Implementation_List)	
	bpy.utils.unregister_class(AF_PR_AssetFetch)


	del bpy.types.WindowManager.af

# Templates
class AF_PR_Generic_String(bpy.types.PropertyGroup):
	value: bpy.props.StringProperty()

class AF_PR_Fixed_Query(bpy.types.PropertyGroup):
	uri: bpy.props.StringProperty
	method: bpy.props.EnumProperty(items=http_method_enum)
	payload: bpy.props.CollectionProperty(type=AF_PR_Generic_String)

class AF_PR_Parameter(bpy.types.PropertyGroup):
	type: bpy.props.EnumProperty(items=
							  [
								  ("text","text","text"),
								  ("boolean","boolean","boolean"),
								  ("fixed","fixed","fixed"),
								  ("select","select","select"),
								  ("multiselect","multiselect","multiselect")
							  ])
	# No name field, taken care of by blender's name property already
	title: bpy.props.StringProperty
	default: bpy.props.StringProperty
	mandatory: bpy.props.BoolProperty
	choices: bpy.props.CollectionProperty(type=AF_PR_Generic_String)
	delimiter: bpy.props.StringProperty

class AF_PR_Variable_Query(bpy.types.PropertyGroup):
	uri: bpy.props.StringProperty
	method: bpy.props.EnumProperty(items=http_method_enum)
	parameters: bpy.props.CollectionProperty(type=AF_PR_Parameter)

class AF_PR_Header(bpy.types.PropertyGroup):
	# name is already taken care of by blender's name field
	default: bpy.props.StringProperty
	is_required: bpy.props.BoolProperty
	is_sensitive: bpy.props.BoolProperty
	prefix: bpy.props.StringProperty
	suffix: bpy.props.StringProperty
	title: bpy.props.StringProperty
	encoding: bpy.props.EnumProperty(items=[
		("plain","plain","plain"),
		("base64","base64","base64")
	])

# Datablocks

class AF_PR_DB_Text(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty
	description: bpy.props.StringProperty

class AF_PR_DB_User(bpy.types.PropertyGroup):
	display_name: bpy.props.StringProperty
	display_tier: bpy.props.StringProperty
	display_icon_uri: bpy.props.StringProperty

class AF_PR_DB_File_Info(bpy.types.PropertyGroup):
	local_path: bpy.props.StringProperty
	length: bpy.props.IntProperty
	extension: bpy.props.StringProperty
	behavior: bpy.props.EnumProperty(items = [
		('file_active','file_active','file_active'),
		('file_passive','file_passive','file_passive'),
		('archive','archive','archive')
	])



	# The actual value entered by the user
	value: bpy.props.StringProperty

class AF_PR_DB_Provider_Configuration(bpy.types.PropertyGroup):
	headers: bpy.props.CollectionProperty(type=AF_PR_Header)
	connection_status_query: bpy.props.PointerProperty(type=AF_PR_Fixed_Query)
	header_acquisition_uri: bpy.props.StringProperty
	header_acquisition_uri_title: bpy.props.StringProperty

class AF_PR_DB_Provider_Reconfiguration(bpy.types.PropertyGroup):
	headers: bpy.props.CollectionProperty(type=AF_PR_Generic_String)

class AF_PR_DB_File_Fetch_From_Archive(bpy.types.PropertyGroup):
	archive_component_id: bpy.props.StringProperty
	component_path: bpy.props.StringProperty

class AF_PR_Web_Reference(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty
	uri: bpy.props.StringProperty
	icon_uri: bpy.props.StringProperty

# class AF_PR_DB_Web_References does not exist, it is handled as a CollectionProperty of individual Web References


# Core elements

class AF_PR_Provider_Initialization(bpy.types.PropertyGroup):
	text: bpy.props.PointerProperty(type=AF_PR_DB_Text)
	user: bpy.props.PointerProperty(type=AF_PR_DB_User)
	# I would have loved to create a class that inherits from the template instead of using it directly.
	# However, inherited properties are not considered, so I have to use the template directly here.
	asset_list_query: bpy.props.PointerProperty(type=AF_PR_Variable_Query)
	headers: bpy.props.CollectionProperty(type=AF_PR_Header)


class AF_PR_Asset(bpy.types.PropertyGroup):
	# No id field, blender's property name takes care of that
	text: bpy.props.PointerProperty(type=AF_PR_DB_Text)
	#...

class AF_PR_Asset_List(bpy.types.PropertyGroup):
	assets: bpy.props.CollectionProperty(type=AF_PR_Asset)

class AF_PR_Component(bpy.types.PropertyGroup):
	file_info:bpy.props.PointerProperty(type=AF_PR_DB_File_Info)

class AF_PR_Implementation(bpy.types.PropertyGroup):
	# No id field, blender's property name takes care of that
	components: bpy.props.CollectionProperty(type=AF_PR_Component)

class AF_PR_Implementation_List(bpy.types.PropertyGroup):
	implementation: bpy.props.CollectionProperty(type=AF_PR_Implementation)

# Final AssetFetch property

class AF_PR_AssetFetch(bpy.types.PropertyGroup):
	last_response_http_code: bpy.props.IntProperty
	last_response_meta_message: bpy.props.StringProperty
	current_init_url: bpy.props.StringProperty
	current_provider_initialization: bpy.props.PointerProperty(type=AF_PR_Provider_Initialization)
	current_asset_list: bpy.props.PointerProperty(type=AF_PR_Asset_List)
	current_asset: bpy.props.PointerProperty(type=AF_PR_Asset)
	current_implementation_list: bpy.props.PointerProperty(type=AF_PR_Implementation_List)
	current_implementation: bpy.props.PointerProperty(type=AF_PR_Implementation)