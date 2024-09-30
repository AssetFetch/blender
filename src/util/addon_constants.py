"""This module contains constants that are used internally by the addon."""

from enum import Enum


class AF_ConnectionState(Enum):
	pending = "pending"
	awaiting_input = "awaiting_input"
	connected = "connected"
	connection_error = "connection_error"

	@staticmethod
	def property_items():
		return [
			("pending", "Pending", "No connection attempt has been made yet"),
			("awaiting_input", "Awaiting Input", "Configuration values are required in order to connect"),  # Used if the provider requires specific headers
			("connected", "Connected", "The connection has been established"),
			("connection_error", "Connection Error", "An error occured while connecting to the provider")
		]


class AF_ImportActionState(Enum):
	pending = "pending"
	running = "running"
	completed = "completed"
	failed = "failed"
	canceled = "canceled"

	def icon_string(self):
		if self.value == "pending":
			return "CHECKBOX_DEHLT"
		if self.value == "running":
			return "SORTTIME"
		if self.value == "completed":
			return "CHECKBOX_HLT"
		if self.value == "failed":
			return "ERROR"
		if self.value == "canceled":
			return "CANCEL"
		return "ERROR"

	@staticmethod
	def property_items():
		return [
			("pending", "Pending", "The step is waiting to be run."),  #
			("running", "Running", "The step is currently running."),
			("completed", "Completed", "The step has finished successfully."),
			("failed", "Failed", "The step could not finish due to an error."),
			("canceled", "Canceled", "The step was manually canceled by the user.")
		]


class AF_ImportAction(Enum):

	fetch_download = "fetch_download"
	fetch_from_zip_archive = "fetch_from_zip_archive"

	import_obj_from_local_path = "import_obj_from_local_path"
	import_usd_from_local_path = "import_usd_from_local_path"
	import_loose_material_map_from_local_path = "import_loose_material_map_from_local_path"
	import_loose_environment_from_local_path = "import_loose_environment_from_local_path"

	unlock = "unlock"

	create_directory = "create_directory"

	def icon_string(self):

		icons = {
			AF_ImportAction.fetch_download: "IMPORT",
			AF_ImportAction.fetch_from_zip_archive: "FILE_ARCHIVE",
			AF_ImportAction.import_obj_from_local_path: "MESH_CUBE",
			AF_ImportAction.import_usd_from_local_path: "MESH_CUBE",
			AF_ImportAction.import_loose_material_map_from_local_path: "MATERIAL",
			AF_ImportAction.import_loose_environment_from_local_path: "WORLD",
			AF_ImportAction.unlock: "UNLOCKED",
			AF_ImportAction.create_directory: "NEWFOLDER"
		}

		if self in icons.keys():
			return icons[self]

		return "PREFERENCES"

	@staticmethod
	def property_items():
		return [

			# The comments behind each item describe the config keys used for it.

			# File actions
			("fetch_download", "Download File", "Downloads a file from the internet."),
			("fetch_from_zip_archive", "Extract File From ZIP Archive", "Extracts a file from a ZIP archive."),

			# Import actions
			("import_obj_from_local_path", "Import OBJ", "Imports content from an OBJ file."),
			("import_usd_from_local_path", "Import USD", "Imports content from a USD file."),
			("import_loose_material_map_from_local_path", "Import Material Map", "Adds a material map to a new or existing material."),
			("import_loose_environment_from_local_path", "Import Environment Map", "Imports an HDRI environment."),

			# Unlock actions
			("unlock", "Unlock Resource", "Unlocks a resource from the provider, so that it can be downloaded."),

			# Misc actions
			("create_directory", "Create Directory", "Creates a directory."),
		]


class AF_BlenderDataTypes(Enum):
	actions = "actions"
	armatures = "armatures"
	brushes = "brushes"
	cache_files = "cache_files"
	cameras = "cameras"
	collections = "collections"
	curves = "curves"
	fonts = "fonts"
	grease_pencils = "grease_pencils"
	hair_curves = "hair_curves"
	images = "images"
	lattices = "lattices"
	lightprobes = "lightprobes"
	lights = "lights"
	linestyles = "linestyles"
	masks = "masks"
	materials = "materials"
	meshes = "meshes"
	metaballs = "metaballs"
	movieclips = "movieclips"
	node_groups = "node_groups"
	objects = "objects"
	paint_curves = "paint_curves"
	palettes = "palettes"
	particles = "particles"
	pointclouds = "pointclouds"
	scenes = "scenes"
	screens = "screens"
	simulations = "simulations"
	sounds = "sounds"
	speakers = "speakers"
	texts = "texts"
	textures = "textures"
	volumes = "volumes"
	workspaces = "workspaces"
	worlds = "worlds"

	@staticmethod
	def property_items():
		return [
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
		]
