import logging
import bpy,os

from .updates import *
from .templates import *
from .datablocks import *
from ..util.addon_constants import *

LOGGER = logging.getLogger("af.property.core")
LOGGER.setLevel(logging.DEBUG)

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
	state:bpy.props.EnumProperty(default="pending",items=AF_ConnectionState.property_items())

class AF_PR_Asset(bpy.types.PropertyGroup):
	# No id field, blender's property name takes care of that
	text: bpy.props.PointerProperty(type=AF_PR_TextBlock)
	implementation_list_query: bpy.props.PointerProperty(type=AF_PR_VariableQuery)
	preview_image_thumbnail: bpy.props.PointerProperty(type=AF_PR_PreviewImageThumbnailBlock)

class AF_PR_AssetList(bpy.types.PropertyGroup):
	assets: bpy.props.CollectionProperty(type=AF_PR_Asset)
	# Datablocks...

	# If the list is empty this field decides whether it is empty because there were no results (True)
	# or because it simply hasn't been queried yet (False)
	already_queried: bpy.props.BoolProperty(default=False)

	def configure(self,asset_list):
		af = bpy.context.window_manager.af

		self.assets.clear()
		for asset in asset_list['assets']:
			asset_entry = self.assets.add()
			asset_entry.name = asset['id']

			# Text
			if "text" in asset['data']:
				asset_entry.text.configure(asset['data']['text'])
			
			# Implementations Query
			if "implementation_list_query" in asset['data']:
				asset_entry.implementation_list_query.configure(asset['data']['implementation_list_query'],update_target=AF_VariableQueryUpdateTarget.update_implementation_list_parameter)

			if "preview_image_thumbnail" in asset['data']:
				asset_entry.preview_image_thumbnail.configure(asset['data']['preview_image_thumbnail'])

		af.current_asset_list_index = 0

		# Indicate that the asset list has already been fetched
		# (This becomes important if it happens to contain 0 elements)
		self.already_queried = True

		# Reset implementations list
		# (Again, indicate that the implementation list hasn't been fetched)
		af.current_implementation_list.implementations.clear()
		af.current_implementation_list.already_queried = False

class AF_PR_BlenderResource(bpy.types.PropertyGroup):
	# object name is handled by name property
	kind: bpy.props.EnumProperty(items=[
		("material","material","material"),
		("object","object","object")
	])

class AF_PR_Component(bpy.types.PropertyGroup):

	text: bpy.props.PointerProperty(type=AF_PR_TextBlock)

	file_info:bpy.props.PointerProperty(type=AF_PR_FileInfoBlock)
	file_handle:bpy.props.PointerProperty(type=AF_PR_FileHandleBlock)
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
	action: bpy.props.EnumProperty(items=AF_ImportAction.property_items())
	config:bpy.props.CollectionProperty(type=AF_PR_GenericString)
	state: bpy.props.EnumProperty(items=AF_ImportActionState.property_items())
	completion: bpy.props.FloatProperty(default=0.0,max=1.0,min=0.0)

	#def set_action(self,action:AF_ImportAction):
	#	self.action = action.value
	#	return self

	def set_config_value(self,key:str,value:str):
		new_conf = self.config.add()
		new_conf.name = key
		new_conf.value = value
		return self
	
	### TODO: Remove old functions and replace with draw_ui
	def get_action_title(self):
		return self.bl_rna.properties['action'].enum_items[self.action].name
	
	def get_action_config(self) -> str:
		out = ""
		for c in self.config:
			out += f"{c.name}={c.value} "
		return out
	
	def get_config_as_function_parameters(self):
		out = {}
		for c in self.config:
			out[c.name] = str(c.value)
		return out

	# File Actions
 
	def configure_fetch_download(self,component_id):
		"""Configures this step as a fetch_download step."""
		self.action = AF_ImportAction.fetch_download.value
		self.config.clear()
		self.set_config_value("component_id",component_id)
 
	def configure_fetch_from_zip_archive(self,component_id):
		"""Configures this step as a fetch_from_zip_archive step."""
		self.action = AF_ImportAction.fetch_from_zip_archive.value
		self.config.clear()
		self.set_config_value("component_id",component_id)

	# Import Actions

	def configure_import_obj_from_local_path(self, component_id):
		"""Configures this step as an import_obj_from_local_path step."""
		self.action = AF_ImportAction.import_obj_from_local_path.value
		self.config.clear()
		self.set_config_value("component_id", component_id)

	def configure_import_usd_from_local_path(self, component_id):
		"""Configures this step as an import_usd_from_local_path step."""
		self.action = AF_ImportAction.import_usd_from_local_path.value
		self.config.clear()
		self.set_config_value("component_id", component_id)

	def configure_import_loose_material_map_from_local_path(self, component_id):
		"""Configures this step as an import_loose_material_map_from_local_path step."""
		self.action = AF_ImportAction.import_loose_material_map_from_local_path.value
		self.config.clear()
		self.set_config_value("component_id", component_id)

	def configure_import_loose_environment_from_local_path(self, component_id):
		"""Configures this step as an import_loose_environment_from_local_path step."""
		self.action = AF_ImportAction.import_loose_environment_from_local_path.value
		self.config.clear()
		self.set_config_value("component_id", component_id)

	# Unlock Actions

	def configure_unlock(self, query_id):
		"""Configures this step as an unlock step."""
		self.action = AF_ImportAction.unlock.value
		self.config.clear()
		self.set_config_value("query_id", query_id)

	def configure_unlock_get_download_data(self, component_id):
		"""Configures this step as an unlock_get_download_data step."""
		self.action = AF_ImportAction.unlock_get_download_data.value
		self.config.clear()
		self.set_config_value("component_id", component_id)

	# Misc Actions

	def configure_create_directory(self,directory):
		"""Configures this step as a create_directory step."""
		self.action = AF_ImportAction.create_directory.value
		self.config.clear()
		self.set_config_value("directory",directory)
		

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
	expected_charges: bpy.props.FloatProperty(default=0)
	local_directory: bpy.props.StringProperty()

	def get_completion_ratio(self) -> float:
		"""Returns number between 0 and 1 to indicate the import progress of this implementation."""
		return float(self.get_step_count()) / float(self.get_completed_step_count())

	def get_current_step(self) -> AF_PR_ImplementationImportStep | None:
		"""Finds the first non-completed step in the implementation and returns it."""
		for s in self.import_steps:
			if s.state != AF_ImportActionState.completed.value:
				return s
		return None
			
	def reset_state(self):
		"""Resets all steps back to 'pending'."""
		for s in self.import_steps:
			s.state = AF_ImportActionState.pending.value

	def get_step_count(self) -> int:
		return len(self.import_steps)

	def get_completed_step_count(self) -> int:
		completed_steps = 0
		for s in self.import_steps:
			if s.state == AF_ImportActionState.completed.value:
				completed_steps +=1
		return completed_steps
		

	def get_component_by_id(self,component_id:str) -> AF_PR_Component:
		for c in self.components:
			if c.name == component_id:
				return c
		raise Exception(f"No component with id {component_id} could be found.")
	
	def configure(self,incoming_impl):

		# Fill the implementation with data from the HTTP endpoint

		# Implementation id
		if "id" not in incoming_impl:
			raise Exception("Implementation is missing and id.")
		self.name = incoming_impl['id']

		# Component data
		#if "components" not in incoming_impl or len(incoming_impl['components']) < 1:
		#	raise Exception("This implementation has no components.")
		for provider_comp in incoming_impl['components']:
			
			blender_comp = self.components.add()

			# For clarity:
			# provider_comp -> the component data sent by the provider
			# blender_comp -> the blender bpy property this component gets turned into
			# pcd -> shorthand for "provider component data"
			pcd = provider_comp['data']
			
			# Component id
			if "id" not in provider_comp:
				raise Exception("A component is missing an id.")
			blender_comp.name = provider_comp['id']

			recognized_datablock_names = [

				"file_info",
				"file_handle",
				"file_fetch.download",
				"file_fetch.download_post_unlock",
				"file_fetch.from_archive",

				"loose_environment",
				"loose_material.define",
				"loose_material.apply",

				"format.blend",
				"format.usd",
				"format.obj",

				"text"
				
				]
			
			# Unsupported datablocks which lead to a warning
			for key in pcd.keys():
				if key not in recognized_datablock_names:
					self.validation_messages.add().set("warn",f"Datablock {key} in {blender_comp.name} has not been recognized and will be ignored.")
			
			# Configure datablocks
			for key in recognized_datablock_names:
				if key in pcd:
					block = getattr(blender_comp,key.replace(".","_"))
					block.is_set = True
					block.configure(pcd[key])
				else:
					# Some datablocks are required and get tested for here.
					if key in ['file_info','file_handle']:
						raise Exception(f"{blender_comp.name} is missing a {key} datablock.")
		return self

class AF_PR_ImplementationList(bpy.types.PropertyGroup):
	implementations: bpy.props.CollectionProperty(type=AF_PR_Implementation)
	unlock_queries: bpy.props.PointerProperty(type=AF_PR_UnlockQueriesBlock)

	# If the list is empty this field decides whether it is empty because there were no results (True)
	# or because it simply hasn't been queried yet (False)
	already_queried: bpy.props.BoolProperty(default=False)

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
		self.already_queried = True

# Final AssetFetch property

class AF_PR_AssetFetch(bpy.types.PropertyGroup):
	current_init_url: bpy.props.StringProperty(description="Init",update=update_init_url)
	current_connection_state: bpy.props.PointerProperty(type=AF_PR_ConnectionStatus)
	current_provider_initialization: bpy.props.PointerProperty(type=AF_PR_ProviderInitialization)
	current_asset_list: bpy.props.PointerProperty(type=AF_PR_AssetList)
	current_asset_list_index: bpy.props.IntProperty(update=update_asset_list_index)
	current_implementation_list: bpy.props.PointerProperty(type=AF_PR_ImplementationList)
	current_implementation_list_index: bpy.props.IntProperty(update=update_implementation_list_index)
	
	download_directory: bpy.props.StringProperty(default=os.path.join(os.path.expanduser('~'),"AssetFetch"))
	ui_image_directory: bpy.props.StringProperty(default=os.path.join(tempfile.gettempdir(),"af-ui-img"))

	#current_import_execution_progress : bpy.props.FloatProperty(max=1.0,min=0.0)

	#progress_all_steps : bpy.props.FloatProperty(max=1,min=0)
	#progress_current_step : bpy.props.FloatProperty(max=1,min=1)

	def get_current_asset(self) -> AF_PR_Asset | None:
		
		if self.current_asset_list_index < 0 | self.current_asset_list_index >= len(self.current_asset_list):
			raise Exception("Invalid index for current asset list.")

		return self.current_asset_list.assets[self.current_asset_list_index]
	
	def get_current_implementation(self) -> AF_PR_Implementation:

		if self.current_implementation_list_index < 0 | self.current_implementation_list_index >= len(self.current_implementation_list):
			raise Exception("Invalid index for current implementation list.")

		return self.current_implementation_list.implementations[self.current_implementation_list_index]
	
