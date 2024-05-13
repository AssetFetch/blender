import bpy
from ..util.http import *

from .updates import *

http_method_enum = [('get', 'GET', 'HTTP GET'), ('post', 'POST', 'HTTP POST')]


class AF_PR_GenericString(bpy.types.PropertyGroup):
	"""A wrapper for the StringProperty to make it usable as a propertyGroup."""
	value: bpy.props.StringProperty()

	def set(self, value):
		self.value = value

	def __str__(self) -> str:
		return str(self.value)


class AF_PR_FixedQuery(bpy.types.PropertyGroup):
	uri: bpy.props.StringProperty()
	method: bpy.props.EnumProperty(items=http_method_enum)
	payload: bpy.props.CollectionProperty(type=AF_PR_GenericString)
	is_set: bpy.props.BoolProperty(default=False)

	def configure(self, fixed_query):
		self.uri = fixed_query['uri']
		self.method = fixed_query['method']
		if "payload" in fixed_query and fixed_query['payload'] != None:
			for p in fixed_query['payload'].keys():
				par = self.payload.add()
				par.name = p
				par.value = fixed_query['payload'][p]
		self.is_set = True

	def to_http_query(self) -> AF_HttpQuery:
		parameters = {}
		for p in self.payload:
			parameters[p.name] = p.value
		return AF_HttpQuery(uri=self.uri, method=self.method, parameters=parameters)


update_target_enum = AF_VariableQueryUpdateTarget.to_property_enum()


class AF_PR_TextParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	default: bpy.props.StringProperty()
	value: bpy.props.StringProperty(update=update_variable_query_parameter)
	update_target: bpy.props.EnumProperty(items=update_target_enum)


#class AF_PR_IntegerParameter(bpy.types.PropertyGroup):
#	title: bpy.props.StringProperty()
#	default: bpy.props.StringProperty()
#	value: bpy.props.IntProperty(update=update_variable_query_parameter)
#	update_target: bpy.props.EnumProperty(items=update_target_enum)
#
#class AF_PR_FloatParameter(bpy.types.PropertyGroup):
#	title: bpy.props.StringProperty()
#	default: bpy.props.StringProperty()
#	value: bpy.props.FloatProperty(update=update_variable_query_parameter)
#	update_target: bpy.props.EnumProperty(items=update_target_enum)


class AF_PR_BoolParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	default: bpy.props.BoolProperty()
	value: bpy.props.BoolProperty(update=update_variable_query_parameter)
	update_target: bpy.props.EnumProperty(items=update_target_enum)


class AF_PR_FixedParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	value: bpy.props.StringProperty()


def select_property_enum_items(property, context):
	out = []
	for c in property.choices:
		out.append((c.value, c.title, c.title))
	return out


class AF_PR_SelectParameterChoice(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	value: bpy.props.StringProperty()


class AF_PR_SelectParameter(bpy.types.PropertyGroup):
	title: bpy.props.StringProperty()
	default: bpy.props.StringProperty()
	choices: bpy.props.CollectionProperty(type=AF_PR_SelectParameterChoice)
	value: bpy.props.EnumProperty(items=select_property_enum_items, update=update_variable_query_parameter)
	update_target: bpy.props.EnumProperty(items=update_target_enum)


class AF_PR_VariableQuery(bpy.types.PropertyGroup):
	uri: bpy.props.StringProperty()
	method: bpy.props.EnumProperty(items=http_method_enum)
	parameters_text: bpy.props.CollectionProperty(type=AF_PR_TextParameter)
	parameters_boolean: bpy.props.CollectionProperty(type=AF_PR_BoolParameter)
	#parameters_float: bpy.props.CollectionProperty(type=AF_PR_FloatParameter)
	#parameters_int: bpy.props.CollectionProperty(type=AF_PR_IntegerParameter)
	parameters_fixed: bpy.props.CollectionProperty(type=AF_PR_FixedParameter)
	parameters_select: bpy.props.CollectionProperty(type=AF_PR_SelectParameter)

	def configure(self, variable_query, update_target: AF_VariableQueryUpdateTarget = AF_VariableQueryUpdateTarget.update_nothing):

		self.uri = ""
		update_target = update_target.value

		self.parameters_text.clear()
		self.parameters_boolean.clear()
		#self.parameters_float.clear()
		#self.parameters_int.clear()
		self.parameters_fixed.clear()
		self.parameters_select.clear()

		self.uri = variable_query['uri']
		self.method = variable_query['method']

		for p in variable_query['parameters']:

			# Text parameters
			if p['type'] == "text":
				new_parameter = self.parameters_text.add()
				new_parameter.title = p['title']
				new_parameter.name = p['id']
				new_parameter.update_target = update_target
				if p['default']:
					new_parameter.value = p['default']

			# Bool parameters
			if p['type'] == "boolean":
				new_parameter = self.parameters_text.add()
				new_parameter.title = p['title']
				new_parameter.name = p['id']
				new_parameter.update_target = update_target
				if p['default']:
					new_parameter.value = p['default'] == "1"
			# Fixed parameters
			if p['type'] == "fixed":
				new_parameter = self.parameters_fixed.add()
				new_parameter.title = p['title']
				new_parameter.name = p['id']
				new_parameter.update_target = update_target
				new_parameter.default = p['default']
				new_parameter.value = p['default']

			# Select parameters
			if p['type'] == "select":
				new_parameter = self.parameters_select.add()
				new_parameter.title = p['title']
				new_parameter.name = p['id']
				new_parameter.update_target = update_target
				for c in p['choices']:
					new_choice = new_parameter.choices.add()
					new_choice.value = c['value']
					new_choice.title = c['title']

		return self

	def to_http_query(self) -> AF_HttpQuery:
		parameters = {}

		# Text parameters
		for par in self.parameters_text:
			parameters[par.name] = str(par.value)

		for par in self.parameters_boolean:
			val = "0"
			if par.value:
				val = "1"
			parameters[par.name] = val

		# Float parameters
		#for par in self.parameters_float:
		#	parameters[par.name] = str(par.value)

		# Integer parameters
		#for par in self.parameters_float:
		#	parameters[par.name] = str(par.value)

		# Fixed Parameters
		for par in self.parameters_fixed:
			parameters[par.name] = str(par.value)

		# Select Parameters
		for par in self.parameters_select:
			if par.value != "<none>":
				parameters[par.name] = str(par.value)

		# Ignoring multi-select for now

		return AF_HttpQuery(uri=self.uri, method=self.method, parameters=parameters)

	def draw_ui(self, layout : bpy.types.UILayout) -> None:

		# Text parameters
		for asset_list_parameter in self.parameters_text:
			layout.prop(asset_list_parameter, "value", text=asset_list_parameter["title"])

		# Bool parameters
		for asset_list_parameter in self.parameters_boolean:
			layout.prop(asset_list_parameter, "value", text=asset_list_parameter["title"])

		# Select parameters
		for asset_list_parameter in self.parameters_select:
			layout.prop(asset_list_parameter, "value", text=asset_list_parameter["title"])

		# Fixed parameters
		#for asset_list_parameter in self.parameters_fixed:
		#	row = layout.row()
		#	row.enabled = False
		#	row.prop(asset_list_parameter, "value", text=asset_list_parameter["title"])


class AF_PR_Header(bpy.types.PropertyGroup):
	# name is already taken care of by blender's name field
	default: bpy.props.StringProperty()
	is_required: bpy.props.BoolProperty()
	is_sensitive: bpy.props.BoolProperty()
	prefix: bpy.props.StringProperty()
	suffix: bpy.props.StringProperty()
	title: bpy.props.StringProperty()
	encoding: bpy.props.EnumProperty(items=[("plain", "plain", "plain"), ("base64", "base64", "base64")])

	# The actual value entered by the user
	value: bpy.props.StringProperty(update=update_provider_header)

	def configure(self, header):
		for key in ['name', 'default', 'is_required', 'is_sensitive', 'prefix', 'suffix', 'title', 'encoding']:
			if key in header:
				setattr(self, key, header[key])
		self.value = self.default
