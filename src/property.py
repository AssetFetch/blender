import os
from typing import Dict
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

# Update functions
def property_update_handler(property,context):
	if "update_target" in property:
		if property.update_target == "update_implementations_list":
			bpy.ops.af.update_implementations_list()
		if property.update_target == "update_asset_list":
			bpy.ops.af_update_asset_list()

# Templates

http_method_enum = [
			('get','GET','HTTP GET'),
			('post','POST','HTTP POST')
		]		

update_target_enum = [
	('update_implementations_list','update_implementations_list','update_implementations_list'),
	('update_asset_list','update_asset_list','update_asset_list')
]

class AF_PR_GenericBlock:
	"""A class inheriting from AF_PR_GenericBlock means that its parameters
	can be loaded from a dict which is usually the result of parsed json.
	See https://stackoverflow.com/a/2466207 """

	is_set: bpy.props.BoolProperty(default=False)

	def configure(self,initial_data):
		self.is_set = True
		for key in initial_data.keys():
			try:
				setattr(self,key,initial_data[key])
			except Exception as e:
				print(f"skipping {key} because {e}")

class AF_PR_GenericString(bpy.types.PropertyGroup):
	"""A wrapper for the StringProperty to make it usable as a propertyGroup."""
	value: bpy.props.StringProperty()

	def set(self,value):
		self.value = value

	def __str__(self) -> str:
		return str(self.value)
	
class AF_PR_FixedQuery(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	uri: bpy.props.StringProperty()
	method: bpy.props.EnumProperty(items=http_method_enum)
	payload: bpy.props.CollectionProperty(type=AF_PR_GenericString)

	def configure(self,fixed_query):
		self.uri = fixed_query['uri']
		self.method = fixed_query['method']
		for p in fixed_query['payload'].keys():
			par = self.payload.add()
			par.name = p
			par.value = fixed_query['payload'][p]

	def to_http_query(self) -> AF_HttpQuery:
		parameters = {}
		for p in self.payload:
			parameters[p.name] = p.value
		return AF_HttpQuery(uri=self.uri,method=self.method,parameters=parameters)

class AF_PR_TextParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	mandatory: bpy.props.BoolProperty()
	default: bpy.props.StringProperty()
	value: bpy.props.StringProperty(update=property_update_handler)
	update_target: bpy.props.EnumProperty(items=update_target_enum)

class AF_PR_IntegerParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	mandatory: bpy.props.BoolProperty()
	default: bpy.props.StringProperty()
	value: bpy.props.IntProperty(update=property_update_handler)
	update_target: bpy.props.EnumProperty(items=update_target_enum)

class AF_PR_FloatParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	mandatory: bpy.props.BoolProperty()
	default: bpy.props.StringProperty()
	value: bpy.props.FloatProperty(update=property_update_handler)
	update_target: bpy.props.EnumProperty(items=update_target_enum)

class AF_PR_BoolParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	default: bpy.props.BoolProperty()
	mandatory: bpy.props.BoolProperty()
	value: bpy.props.BoolProperty(update=property_update_handler)
	update_target: bpy.props.EnumProperty(items=update_target_enum)

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

	# This class brings its own configure() instead of in heriting from
	# AF_PR_GenericBlock because it is a bit more complicated.
	def configure(self,variable_query):

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

class AF_PR_TextBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	title: bpy.props.StringProperty()
	description: bpy.props.StringProperty()

class AF_PR_UserBlock(bpy.types.PropertyGroup):
	display_name: bpy.props.StringProperty()
	display_tier: bpy.props.StringProperty()
	display_icon_uri: bpy.props.StringProperty()

class AF_PR_FileInfoBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
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

class AF_PR_UnlockBalanceBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	balance: bpy.props.FloatProperty()
	balance_unit: bpy.props.StringProperty()
	balance_refill_uri: bpy.props.StringProperty()

class AF_PR_ProviderReconfigurationBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	headers: bpy.props.CollectionProperty(type=AF_PR_GenericString)

class AF_PR_FileFetchFromArchiveBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	archive_component_id: bpy.props.StringProperty()
	component_path: bpy.props.StringProperty()

# This is not the actual datablock, just one list item within it
class AF_PR_WebReference(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty
	uri: bpy.props.StringProperty
	icon_uri: bpy.props.StringProperty

class AF_PR_UnlockLinkBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	unlock_query_id: bpy.props.StringProperty()
	unlocked_datablocks_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)

	def configure(self,unlock_link):
		self.unlock_query_id = unlock_link['unlock_query_id']
		self.unlocked_datablocks_query.configure(unlock_link['unlocked_datablocks_query'])

class AF_PR_LooseEnvironmentBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	projection: bpy.props.EnumProperty(items=[
		("equirectangular","equirectangular","equirectangular"),
		("mirror_ball","mirror_ball","mirror_ball")
	])

class AF_PR_LooseMaterialDefineBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	material_name: bpy.props.StringProperty()
	map: bpy.props.EnumProperty(items=[
		("albedo", "Albedo", "Albedo"),
		("roughness", "Roughness", "Roughness"),
		("metallic", "Metallic", "Metallic"),
		("diffuse", "Diffuse", "Diffuse"),
		("glossiness", "Glossiness", "Glossiness"),
		("specular", "Specular", "Specular"),
		("height", "Height", "Height"),
		("normal+y", "Normal +Y", "Normal +Y"),
		("normal-y", "Normal -Y", "Normal -Y"),
		("opacity", "Opacity", "Opacity"),
		("ambient_occlusion", "Ambient Occlusion", "Ambient Occlusion"),
		("emission", "Emission", "Emission"),
	])
	colorspace: bpy.props.EnumProperty(items=[
		("srgb","sRGB","sRGB"),
		("linear","linear","linear")
	])

class AF_PR_LooseMaterialApplyElement(bpy.types.PropertyGroup):
	material_name: bpy.props.StringProperty()
	apply_selectively_to: bpy.props.StringProperty()

class AF_PR_LooseMaterialApplyBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	items: bpy.props.CollectionProperty(type=AF_PR_LooseMaterialApplyElement)

	def configure(self,loose_material_apply):
		for elem in loose_material_apply:
			new_item = self.items.add()
			new_item.material_name = elem['material_name']
			if "apply_selectively_to" in elem and elem['apply_selectively_to'] != None:
				new_item.apply_selectively_to = elem['apply_selectively_to']

class AF_PR_FormatBlendTarget(bpy.types.PropertyGroup):
	names: bpy.props.CollectionProperty(type=AF_PR_GenericString)
	kind: bpy.props.EnumProperty(items=[
		("actions", "Actions", "Actions"),
		("armatures", "Armatures", "Armatures"),
		("brushes", "Brushes", "Brushes"),
		("cache_files", "Cache Files", "Cache Files"),
		("cameras", "Cameras", "Cameras"),
		("collections", "Collections", "Collections"),
		("curves", "Curves", "Curves"),
		("fonts", "Fonts", "Fonts"),
		("grease_pencils", "Grease Pencils", "Grease Pencils"),
		("hair_curves", "Hair Curves", "Hair Curves"),
		("images", "Images", "Images"),
		("lattices", "Lattices", "Lattices"),
		("lightprobes", "Lightprobes", "Lightprobes"),
		("lights", "Lights", "Lights"),
		("linestyles", "Linestyles", "Linestyles"),
		("masks", "Masks", "Masks"),
		("materials", "Materials", "Materials"),
		("meshes", "Meshes", "Meshes"),
		("metaballs", "Metaballs", "Metaballs"),
		("movieclips", "Movieclips", "Movieclips"),
		("node_groups", "Node Groups", "Node Groups"),
		("objects", "Objects", "Objects"),
		("paint_curves", "Paint Curves", "Paint Curves"),
		("palettes", "Palettes", "Palettes"),
		("particles", "Particles", "Particles"),
		("pointclouds", "Pointclouds", "Pointclouds"),
		("scenes", "Scenes", "Scenes"),
		("screens", "Screens", "Screens"),
		("simulations", "Simulations", "Simulations"),
		("sounds", "Sounds", "Sounds"),
		("speakers", "Speakers", "Speakers"),
		("texts", "Texts", "Texts"),
		("textures", "Textures", "Textures"),
		("volumes", "Volumes", "Volumes"),
		("workspaces", "Workspaces", "Workspaces"),
		("worlds", "Worlds", "Worlds"),
	])

class AF_PR_FormatBlendBlock(bpy.types.PropertyGroup):
	version: bpy.props.StringProperty()
	is_asset: bpy.props.BoolProperty()
	targets: bpy.props.CollectionProperty(type=AF_PR_FormatBlendTarget)

	# The complex target object means that we need a custom config method
	def configure(self,format_blend):
		self.version = format_blend['version']
		self.is_asset = format_blend['is_asset']
		for t in format_blend['targets']:
			new_target = self.targets.add()
			new_target.kind = t['kind']
			for n in t['names']:
				new_name = new_target.names.add()
				new_name.value = n

class AF_PR_FormatUsdBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	is_crate: bpy.props.BoolProperty()

class AF_PR_FormatObjBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	up_axis: bpy.props.StringProperty()

	blender_objects: bpy.props.CollectionProperty(type=AF_PR_GenericString)

# Single element of the unlock_queries list
class AF_PR_UnlockQuery(bpy.types.PropertyGroup):
	# ID is handled by blenders property name
	unlocked: bpy.props.BoolProperty(default=False)
	price: bpy.props.FloatProperty()
	unlock_query: bpy.props.PointerProperty(type=AF_PR_FixedQuery)
	unlock_query_fallback_uri: bpy.props.StringProperty()

	def configure(self,unlock_query):
		self.name = unlock_query['id']
		if "unlocked" in unlock_query:
			self.unlocked = unlock_query['unlocked']
		if "price" in unlock_query:
			self.price = unlock_query['price']
		if "unlock_query" in unlock_query:
			self.unlock_query.configure(unlock_query['unlock_query'])
		if "unlock_query_fallback_uri" in unlock_query and unlock_query['unlock_query_fallback_uri']:
			self.unlock_query_fallback_uri = unlock_query['unlock_query_fallback_uri']

class AF_PR_UnlockQueriesBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	items: bpy.props.CollectionProperty(type=AF_PR_UnlockQuery)

	def configure(self,unlock_queries):
		for q in unlock_queries:
			self.items.add().configure(q)

class AF_PR_PreviewImageThumbnailBlock(bpy.types.PropertyGroup,AF_PR_GenericBlock):
	alt: bpy.props.StringProperty()
	uris: bpy.props.CollectionProperty(type=AF_PR_GenericString)
	chosen_resolution: bpy.props.IntProperty()
	temp_file_id: bpy.props.StringProperty()
	icon_id: bpy.props.IntProperty(default=-1)

	def configure(self, preview_image_thumbnail):
		self.is_set = True
		if "alt" in preview_image_thumbnail:
			self.alt = preview_image_thumbnail['alt']
		for resolution in preview_image_thumbnail['uris'].keys():
			new_res = self.uris.add()
			new_res.name = resolution
			new_res.value = preview_image_thumbnail['uris'][resolution]

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
	preview_image_thumbnail: bpy.props.PointerProperty(type=AF_PR_PreviewImageThumbnailBlock)
	#...

class AF_PR_AssetList(bpy.types.PropertyGroup):
	assets: bpy.props.CollectionProperty(type=AF_PR_Asset)
	# Datablocks...

class AF_PR_BlenderResource(bpy.types.PropertyGroup):
	# object name is handled by name property
	kind: bpy.props.EnumProperty(items=[
		("material","material","material"),
		("object","object","object")
	])

class AF_PR_Component(bpy.types.PropertyGroup):

	text: bpy.props.PointerProperty(type=AF_PR_TextBlock)

	file_info:bpy.props.PointerProperty(type=AF_PR_FileInfoBlock)
	file_fetch_download:bpy.props.PointerProperty(type=AF_PR_FixedQuery)
	file_fetch_from_archive: bpy.props.PointerProperty(type=AF_PR_FileFetchFromArchiveBlock)
	unlock_link: bpy.props.PointerProperty(type=AF_PR_UnlockLinkBlock)

	loose_environment: bpy.props.PointerProperty(type=AF_PR_LooseEnvironmentBlock)
	loose_material_define: bpy.props.PointerProperty(type=AF_PR_LooseMaterialDefineBlock)
	loose_material_apply: bpy.props.PointerProperty(type=AF_PR_LooseMaterialApplyBlock)

	format_blend: bpy.props.PointerProperty(type=AF_PR_FormatBlendBlock)
	format_obj: bpy.props.PointerProperty(type=AF_PR_FormatObjBlock)
	format_usd: bpy.props.PointerProperty(type=AF_PR_FormatUsdBlock)

	def configure(self,component):
		pass



class AF_PR_ImplementationImportStep(bpy.types.PropertyGroup):
	action: bpy.props.EnumProperty(items=[

		# The comments behind each item describe the config keys used for it.

		# File actions
		("fetch_download","Download File","Download a file."), # component_id
		("fetch_download_unlocked","Download Unlocked File","Download a file after it has been unlocked."), # component_id
		("fetch_from_archive","Load File From Archive","Load a file from an archive."),

		# Import actions
		("import_obj_from_local_path","Import OBJ","Imports obj file from local path."), # component_id
		("import_usd_from_local_path","Import USD","Imports USDA/C/Z file from a local path."), # component_id
		("import_loose_material_map_from_local_path","Import loose material map","Adds a loose material map from a local path to a material."), # component_id
		("import_loose_environment_from_local_path","Import a loose environment","Imports a loose HDR/EXR/... file and creates a world from it."), # component_id

		# Misc actions
		("directory_create","Create Directory","Create a directory."), # directory
		("unlock","Unlock Resource","") # query_id
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
	
	def get_action_title(self):
		return self.bl_rna.properties['action'].enum_items[self.action].name
	
	def get_action_config(self) -> str:
		out = ""
		for c in self.config:
			out += f"{c.name}={c.value} "
		return out

class AF_PR_ImplementationValidationMessage(bpy.types.PropertyGroup):
	text : bpy.props.StringProperty()
	kind: bpy.props.EnumProperty(items=[
		("info","info","info"),
		("warn","warning","warning"),
		("crit","critical","critical")
	])

	def set(self,kind:str,text:str):
		self.text = text
		self.kind = kind
		return self

class AF_PR_Implementation(bpy.types.PropertyGroup):
	# No id field, blender's property name takes care of that
	components: bpy.props.CollectionProperty(type=AF_PR_Component)
	is_valid: bpy.props.BoolProperty()
	validation_messages: bpy.props.CollectionProperty(type=AF_PR_ImplementationValidationMessage)
	import_steps: bpy.props.CollectionProperty(type=AF_PR_ImplementationImportStep)
	local_directory: bpy.props.StringProperty()

	def get_component_by_id(self,component_id:str) -> AF_PR_Component:
		for c in self.components:
			if c.name == component_id:
				return c
		raise Exception(f"No component with id {component_id} could be found.")
	
	def configure(self,incoming_impl):
		# -------------------------------------------------------------------------------
		# Fill the implementation with data from the HTTP endpoint

		# Implementation id
		if "id" not in incoming_impl:
			raise Exception("Implementation is missing and id.")
		self.name = incoming_impl['id']

		# Component data
		if "components" not in incoming_impl or len(incoming_impl['components']) < 1:
			raise Exception("This implementation has no components.")
		for provider_comp in incoming_impl['components']:
			
			blender_comp = self.components.add()

			# For clarity:
			# provider_comp -> the component data sent by the provider
			# blender_comp -> the blender bpy property this component gets turned into
			# pcd -> shorthand for "provider component data" (This will appear a lot)
			pcd = provider_comp['data']
			
			# Component id
			if "id" not in provider_comp:
				raise Exception("A component is missing an id.")
			blender_comp.name = provider_comp['id']

			recognized_datablock_names = [

				"file_info",
				"file_fetch.download",
				"file_fetch.from_archive",

				"loose_environment",
				"loose_material_define",
				"loose_material_apply",

				"format.blend",
				"format.usd",
				"format.obj",

				"unlock_link",
				"text"
				
				]
			
			# Unsupported datablocks which lead to a warning
			for key in pcd.keys():
				if key not in recognized_datablock_names:
					self.validation_messages.add().set("warn",f"Datablock {key} in {blender_comp.name} has not been recognized and will be ignored.")
			
			# Configure datablocks
			for key in recognized_datablock_names:
				if key in pcd:
					print(f"setting {blender_comp.name} -> {key}")
					block = getattr(blender_comp,key.replace(".","_"))
					block.is_set = True
					block.configure(pcd[key])
				else:
					# Some datablocks are required and get tested for here.
					if key in ['file_info']:
						raise Exception(f"{blender_comp.name} is missing a {key} datablock.")
		return self

class AF_PR_ImplementationList(bpy.types.PropertyGroup):
	implementations: bpy.props.CollectionProperty(type=AF_PR_Implementation)
	unlock_queries: bpy.props.PointerProperty(type=AF_PR_UnlockQueriesBlock)

	def get_unlock_query_by_id(self,query_id:str) -> AF_PR_UnlockQuery:
		for q in self.unlock_queries.items:
			if q.name == query_id:
				return q
			
		raise Exception(f"No unlocking query with id {query_id} could be found.")
	
	def configure(self,implementation_list):
		# Parse the datablocks for the ImplementationList itself
		if "unlock_queries" in implementation_list['data']:
			self.unlock_queries.is_set = True
			for unlock_query in implementation_list['data']['unlock_queries']:
				self.unlock_queries.items.add().configure(unlock_query)

		for incoming_impl in implementation_list['implementations']:
			new_impl = self.implementations.add()
			new_impl.configure(incoming_impl)	

# Final AssetFetch property

class AF_PR_AssetFetch(bpy.types.PropertyGroup):
	current_init_url: bpy.props.StringProperty(description="Init")
	current_connection_state: bpy.props.PointerProperty(type=AF_PR_ConnectionStatus)
	current_provider_initialization: bpy.props.PointerProperty(type=AF_PR_ProviderInitialization)
	current_asset_list: bpy.props.PointerProperty(type=AF_PR_AssetList)
	current_asset_list_index: bpy.props.IntProperty(update=property_update_handler)
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
	AF_PR_LooseEnvironmentBlock,
	AF_PR_LooseMaterialDefineBlock,
	AF_PR_LooseMaterialApplyElement,
	AF_PR_LooseMaterialApplyBlock,
	AF_PR_FormatBlendTarget,
	AF_PR_FormatBlendBlock,
	AF_PR_FormatUsdBlock,
	AF_PR_FormatObjBlock,
	AF_PR_UnlockQuery,
	AF_PR_UnlockQueriesBlock,
	AF_PR_PreviewImageThumbnailBlock,
	
	AF_PR_ProviderInitialization,
	AF_PR_ConnectionStatus,
	AF_PR_Asset,
	AF_PR_AssetList,
	AF_PR_BlenderResource,
	AF_PR_Component,
	AF_PR_ImplementationImportStep,
	AF_PR_ImplementationValidationMessage,
	AF_PR_Implementation,
	AF_PR_ImplementationList,
	AF_PR_AssetFetch
]