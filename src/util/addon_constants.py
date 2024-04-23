
from enum import Enum


class AF_ConnectionState(Enum):
	pending = "pending"
	awaiting_input = "awaiting_input"
	connected = "connected"
	connection_error = "connection_error"

	@staticmethod
	def property_items():
		return [
		("pending","Pending","No connection attempt has been made yet"),
		("awaiting_input","Awaiting Input","Configuration values are required in order to connect"),
		("connected","Connected","The connection has been established"),
		("connection_error","Connection Error","An error occured while connecting to the provider")
	]

class AF_ImportAction(Enum):
	fetch_download = "fetch_download"
	fetch_download_unlocked = "fetch_download_unlocked"
	fetch_from_zip_archive = "fetch_from_zip_archive"
	import_obj_from_local_path = "import_obj_from_local_path"
	import_usd_from_local_path = "import_usd_from_local_path"
	import_loose_material_map_from_local_path = "import_loose_material_map_from_local_path"
	import_loose_environment_from_local_path = "import_loose_environment_from_local_path"
	directory_create = "directory_create"
	unlock = "unlock"

	@staticmethod
	def property_items():
		return [

		# The comments behind each item describe the config keys used for it.

		# File actions
		("fetch_download","Download File","Download a file."), # component_id
		("fetch_download_unlocked","Download Unlocked File","Download a file after it has been unlocked."), # component_id
		("fetch_from_zip_archive","Load File From Archive","Load a file from an archive."),

		# Import actions
		("import_obj_from_local_path","Import OBJ","Imports obj file from local path."), # component_id
		("import_usd_from_local_path","Import USD","Imports USDA/C/Z file from a local path."), # component_id
		("import_loose_material_map_from_local_path","Import loose material map","Adds a loose material map from a local path to a material."), # component_id
		("import_loose_environment_from_local_path","Import a loose environment","Imports a loose HDR/EXR/... file and creates a world from it."), # component_id

		# Misc actions
		("directory_create","Create Directory","Create a directory."), # directory
		("unlock","Unlock Resource","") # query_id
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