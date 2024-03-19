import os
import bpy

from src.http import AF_HttpQuery

def register():

	for cl in registration_targets:
		bpy.utils.register_class(cl)	

	bpy.types.WindowManager.af = bpy.props.PointerProperty(type=AF_PR_AssetFetch)

def unregister():

	del bpy.types.WindowManager.af

	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)

# Templates

http_method_enum = [
			('get','GET','HTTP GET'),
			('post','POST','HTTP POST')
		]		

		
class AF_PR_GenericString(bpy.types.PropertyGroup):
	"""A wrapper for the StringProperty to make it usable as a propertyGroup."""
	value: bpy.props.StringProperty()

class AF_PR_FixedQuery(bpy.types.PropertyGroup):
	uri: bpy.props.StringProperty()
	method: bpy.props.EnumProperty(items=http_method_enum)
	payload: bpy.props.CollectionProperty(type=AF_PR_GenericString)

	def to_http_query(self) -> AF_HttpQuery:
		return AF_HttpQuery(uri=self.uri,method=self.method,parameters=self.payload)

class AF_PR_TextParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	mandatory: bpy.props.BoolProperty()
	default: bpy.props.StringProperty()
	value: bpy.props.StringProperty()

class AF_PR_IntegerParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	mandatory: bpy.props.BoolProperty()
	default: bpy.props.StringProperty()
	value: bpy.props.IntProperty()

class AF_PR_FloatParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	mandatory: bpy.props.BoolProperty()
	default: bpy.props.StringProperty()
	value: bpy.props.FloatProperty()

class AF_PR_BoolParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	default: bpy.props.BoolProperty()
	mandatory: bpy.props.BoolProperty()
	value: bpy.props.BoolProperty()

class AF_PR_FixedParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	value: bpy.props.StringProperty()

def select_property_enum_items(property,context):
	out = []
	for c in property.choices:
		out.append(
			(c.value,c.value,c.value)
		)
	return out

class AF_PR_SelectParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	default: bpy.props.StringProperty()
	mandatory: bpy.props.BoolProperty()
	choices: bpy.props.CollectionProperty(type=AF_PR_GenericString)
	value: bpy.props.EnumProperty(items=select_property_enum_items)

class AF_PR_MultiSelectItem(bpy.types.PropertyGroup):
	choice: bpy.props.StringProperty()
	active: bpy.props.BoolProperty()

class AF_PR_MultiSelectParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	default: bpy.props.StringProperty()
	delimiter: bpy.props.StringProperty()
	values: bpy.props.CollectionProperty(type=AF_PR_MultiSelectItem)
	mandatory: bpy.props.BoolProperty()

class AF_PR_VariableQuery(bpy.types.PropertyGroup):
	uri: bpy.props.StringProperty()
	method: bpy.props.EnumProperty(items=http_method_enum)
	parameters_text: bpy.props.CollectionProperty(type=AF_PR_TextParameter)
	parameters_boolean: bpy.props.CollectionProperty(type=AF_PR_BoolParameter)
	parameters_float: bpy.props.CollectionProperty(type=AF_PR_FloatParameter)
	parameters_int: bpy.props.CollectionProperty(type=AF_PR_IntegerParameter)
	parameters_fixed: bpy.props.CollectionProperty(type=AF_PR_FixedParameter)
	parameters_select: bpy.props.CollectionProperty(type=AF_PR_SelectParameter)
	parameters_multiselect: bpy.props.CollectionProperty(type=AF_PR_MultiSelectParameter)


	def from_dict(self,variable_query):

		self.uri = ""

		self.parameters_text.clear()
		self.parameters_boolean.clear()
		self.parameters_float.clear()
		self.parameters_int.clear()
		self.parameters_fixed.clear()
		self.parameters_select.clear()
		self.parameters_multiselect.clear()

		self.uri = variable_query['uri']
		self.method = variable_query['method']

		for p in variable_query['parameters']:

			# Text parameters
			if p['type'] in ["text","boolean","integer","float"]:
				new_parameter = self.parameters_text.add()
				new_parameter.title = p['title']
				new_parameter.name = p['name']
				if p['default']:
					new_parameter.value = p['default']
				if p['mandatory']:
					new_parameter.mandatory = p['mandatory']

			if p['type'] == "select":
				new_parameter = self.parameters_select.add()
				new_parameter.title = p['title']
				new_parameter.name = p['name']
				if p['mandatory']:
					new_parameter.mandatory = p['mandatory']
				for c in p['choices']:
					new_choice = new_parameter.choices.add()
					new_choice.value = c

		return self

	def to_http_query(self) -> AF_HttpQuery:
		parameters = {}

		# Text parameters
		for par in self.parameters_text:
			if par.mandatory and par.value is None:
				raise Exception(f"Parameter {par.name} is mandatory but empty.")
			parameters[par.name] = str(par.value)

		# Float parameters
		for par in self.parameters_float:
			if par.mandatory and par.value is None:
				raise Exception(f"Parameter {par.name} is mandatory but empty.")
			parameters[par.name] = str(par.value)

		# Integer parameters
		for par in self.parameters_float:
			if par.mandatory and par.value is None:
				raise Exception(f"Parameter {par.name} is mandatory but empty.")
			parameters[par.name] = str(par.value)

		# Fixed Parameters
		for par in self.parameters_float:
			if par.mandatory and par.value is None:
				raise Exception(f"Parameter {par.name} is mandatory but empty.")
			parameters[par.name] = str(par.value)

		# Select Parameters
		for par in self.parameters_select:
			parameters[par.name] = str(par.value)

		# Ignoring multi-select for now

		return AF_HttpQuery(uri=self.uri,method=self.method,parameters=parameters)
	
	def draw_ui(self,layout) -> None:
		
		# Text parameters
		for asset_list_parameter in self.parameters_text:
			layout.prop(asset_list_parameter,"value",text=asset_list_parameter["name"])
		
		# Select parameters
		for asset_list_parameter in self.parameters_select:
			layout.prop(asset_list_parameter,"value",text=asset_list_parameter["name"])


class AF_PR_Header(bpy.types.PropertyGroup):
	# name is already taken care of by blender's name field
	default: bpy.props.StringProperty()
	is_required: bpy.props.BoolProperty()
	is_sensitive: bpy.props.BoolProperty()
	prefix: bpy.props.StringProperty()
	suffix: bpy.props.StringProperty()
	title: bpy.props.StringProperty()
	encoding: bpy.props.EnumProperty(items=[
		("plain","plain","plain"),
		("base64","base64","base64")
	])

	# The actual value entered by the user
	value: bpy.props.StringProperty()

# Datablocks

class AF_PR_TextBlock(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	description: bpy.props.StringProperty()

class AF_PR_UserBlock(bpy.types.PropertyGroup):
	display_name: bpy.props.StringProperty()
	display_tier: bpy.props.StringProperty()
	display_icon_uri: bpy.props.StringProperty()

class AF_PR_FileInfoBlock(bpy.types.PropertyGroup):
	local_path: bpy.props.StringProperty()
	length: bpy.props.IntProperty()
	extension: bpy.props.StringProperty()
	behavior: bpy.props.EnumProperty(items = [
		('file_active','file_active','file_active'),
		('file_passive','file_passive','file_passive'),
		('archive','archive','archive')
	])

class AF_PR_ProviderConfigurationBlock(bpy.types.PropertyGroup):
	headers: bpy.props.CollectionProperty(type=AF_PR_Header)
	connection_status_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)
	header_acquisition_uri: bpy.props.StringProperty()
	header_acquisition_uri_title: bpy.props.StringProperty()

class AF_PR_UnlockBalanceBlock(bpy.types.PropertyGroup):
	is_set: bpy.props.BoolProperty(default=False)
	balance: bpy.props.FloatProperty()
	balance_unit: bpy.props.StringProperty()
	balance_refill_uri: bpy.props.StringProperty()

class AF_PR_ProviderReconfigurationBlock(bpy.types.PropertyGroup):
	headers: bpy.props.CollectionProperty(type=AF_PR_GenericString)

class AF_PR_FileFetchFromArchiveBlock(bpy.types.PropertyGroup):
	archive_component_id: bpy.props.StringProperty
	component_path: bpy.props.StringProperty

# This is not the actual datablock, just one list item within it
class AF_PR_WebReference(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty
	uri: bpy.props.StringProperty
	icon_uri: bpy.props.StringProperty

class AF_PR_UnlockLinkBlock(bpy.types.PropertyGroup):
	unlock_query_id: bpy.props.StringProperty()
	unlocked_datablocks_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)

# Core elements

class AF_PR_ProviderInitialization(bpy.types.PropertyGroup):
	# The built-in 'name' property takes care of the provider id
	text: bpy.props.PointerProperty(type=AF_PR_TextBlock)
	# I would have loved to create a class that inherits from the template instead of using it directly.
	# However, inherited properties are not considered, so I have to use the template directly here.
	asset_list_query: bpy.props.PointerProperty(type=AF_PR_VariableQuery)
	provider_configuration: bpy.props.PointerProperty(type=AF_PR_ProviderConfigurationBlock)
	user: bpy.props.PointerProperty(type=AF_PR_UserBlock)

class AF_PR_ConnectionStatus(bpy.types.PropertyGroup):
	user: bpy.props.PointerProperty(type=AF_PR_UserBlock)
	unlock_balance: bpy.props.PointerProperty(type=AF_PR_UnlockBalanceBlock)
	state:bpy.props.EnumProperty(default="pending",items=[
		("pending","Pending","No connection attempt has been made yet"),
		("awaiting_input","Awaiting Input","Configuration values are required in order to connect"),
		("connected","Connected","The connection has been established"),
		("connection_error","Connection Error","An error occured while connecting to the provider")
	])

class AF_PR_Asset(bpy.types.PropertyGroup):
	# No id field, blender's property name takes care of that
	text: bpy.props.PointerProperty(type=AF_PR_TextBlock)
	implementation_list_query: bpy.props.PointerProperty(type=AF_PR_VariableQuery)
	#...

class AF_PR_AssetList(bpy.types.PropertyGroup):
	assets: bpy.props.CollectionProperty(type=AF_PR_Asset)
	# Datablocks...

class AF_PR_Component(bpy.types.PropertyGroup):
	file_info:bpy.props.PointerProperty(type=AF_PR_FileInfoBlock)
	file_fetch_download:bpy.props.PointerProperty(type=AF_PR_FixedQuery)
	file_fetch_from_archive: bpy.props.PointerProperty(type=AF_PR_FileFetchFromArchiveBlock)
	unlock_link: bpy.props.PointerProperty(type=AF_PR_UnlockLinkBlock)

class AF_PR_ImportStep(bpy.types.PropertyGroup):
	action: bpy.props.EnumProperty(items=[
		("directory_create","Create Directory","Create a directory."),
		("unlock","Unlock Resource",""),
		("fetch_download","Download File","Download a file."),
		("fetch_download_unlocked","Download Unlocked File","Download a file after it has been unlocked."),
		("fetch_from_archive","Load File From Archive","Load a file from an archive."),
		("import_obj_from_local_path","Import OBJ","Import obj file from local path."),
		("material_create","Create Material","Creates a new Material."),
		("material_add_map","Add Map","Add Map to Material"),
		("material_assign","Assign Material","Assigns a material to an object"),
		("world_create","Create World","Creates a new world/environment."),
		("world_set","Set World Map","Set the environment map for a world.")
	])
	config:bpy.props.CollectionProperty(type=AF_PR_GenericString)

	def set_action(self,action:str):
		self.action = action
		return self

	def set_config_value(self,key:str,value:str):
		new_conf = self.config.add()
		new_conf.name = key
		new_conf.value = value
		return self
	
	def __str__(self) -> str:
		out = self.bl_rna.properties['action'].enum_items[self.action].name
		for c in self.config:
			out += f" ({c.name}: {c.value})"
		return out

class AF_PR_Implementation(bpy.types.PropertyGroup):
	# No id field, blender's property name takes care of that
	components: bpy.props.CollectionProperty(type=AF_PR_Component)
	is_valid: bpy.props.BoolProperty()
	validation_message: bpy.props.StringProperty()
	import_steps: bpy.props.CollectionProperty(type=AF_PR_ImportStep)
	local_directory: bpy.props.StringProperty()

class AF_PR_ImplementationList(bpy.types.PropertyGroup):
	implementations: bpy.props.CollectionProperty(type=AF_PR_Implementation)

# Final AssetFetch property

class AF_PR_AssetFetch(bpy.types.PropertyGroup):
	current_init_url: bpy.props.StringProperty(description="Init")
	current_connection_state: bpy.props.PointerProperty(type=AF_PR_ConnectionStatus)
	current_provider_initialization: bpy.props.PointerProperty(type=AF_PR_ProviderInitialization)
	current_asset_list: bpy.props.PointerProperty(type=AF_PR_AssetList)
	current_asset_list_index: bpy.props.IntProperty()
	current_implementation_list: bpy.props.PointerProperty(type=AF_PR_ImplementationList)
	current_implementation_list_index: bpy.props.IntProperty()
	download_directory: bpy.props.StringProperty(default=os.path.join(os.path.expanduser('~'),"AssetFetch"))


registration_targets = [
	AF_PR_GenericString,
	AF_PR_FixedQuery,
	AF_PR_BoolParameter,
	AF_PR_TextParameter,
	AF_PR_FloatParameter,
	AF_PR_IntegerParameter,
	AF_PR_FixedParameter,
	AF_PR_SelectParameter,
	AF_PR_MultiSelectItem,
	AF_PR_MultiSelectParameter,
	AF_PR_VariableQuery,
	AF_PR_Header,

	AF_PR_TextBlock,
	AF_PR_UserBlock,
	AF_PR_FileInfoBlock,
	AF_PR_ProviderConfigurationBlock,
	AF_PR_ProviderReconfigurationBlock,
	AF_PR_UnlockBalanceBlock,
	AF_PR_FileFetchFromArchiveBlock,
	AF_PR_UnlockLinkBlock,
	
	AF_PR_ProviderInitialization,
	AF_PR_ConnectionStatus,
	AF_PR_Asset,
	AF_PR_AssetList,
	AF_PR_Component,
	AF_PR_ImportStep,
	AF_PR_Implementation,
	AF_PR_ImplementationList,
	AF_PR_AssetFetch
]