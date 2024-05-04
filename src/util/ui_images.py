from . import http
import logging, bpy, os, hashlib, shutil

LOGGER = logging.getLogger("af.util.ui_images")
LOGGER.setLevel(logging.DEBUG)

registry: bpy.utils.previews.ImagePreviewCollection = bpy.utils.previews.new()


def reset_image_cache():
	"""Empties the temporary thumbnail directory and flushes all thumbnails from memory"""

	# Empty temp directory
	if os.path.exists(bpy.context.window_manager.af.ui_image_directory):
		shutil.rmtree(bpy.context.window_manager.af.ui_image_directory)
	os.makedirs(bpy.context.window_manager.af.ui_image_directory, exist_ok=True)

	# Clear icons from memory
	if registry:
		registry.clear()


def get_sha1_hash(string: str):
	try:
		messageDigest = hashlib.sha1(usedforsecurity=False)
		stringM = str(string)
		byteM = bytes(stringM, encoding='utf')
		messageDigest.update(byteM)
		return messageDigest.hexdigest()
	except TypeError:
		raise "String to hash was not compatible"


def get_ui_image_icon_id(uri: str) -> int:
	"""Load an image from the given URL and imports it into Blender as an icon, so that it can be used in UI panels.
	The image is stored in a temporary directory using the sha1 of the URI as its name.
	If the requested file is already on disk then it is not loaded again.
	It returns the 'icon_id' for this image.
	"""

	# Helpful variables
	af = bpy.context.window_manager.af
	uri_hash = get_sha1_hash(uri)
	target_file_location = os.path.join(af.ui_image_directory, uri_hash)

	# Download image, if needed
	if not os.path.exists(target_file_location):
		# Image must be downloaded
		image_query = http.AF_HttpQuery(uri, "get", None)
		image_query.execute_as_file(target_file_location)
		LOGGER.debug(f"Downloaded ui image from {uri} into {target_file_location}")

	# Load image into blender, if needed
	if uri_hash not in registry.keys():
		registry.load(name=uri_hash, path=target_file_location, path_type='IMAGE')
		LOGGER.debug(f"Registered ui image from {target_file_location} with ID {registry[uri_hash].icon_id}")
	#else:
	#	LOGGER.debug(f"Requested ui image {uri} is already loaded with ID {registry[uri_hash].icon_id}")

	# Return the icon id
	return registry[uri_hash].icon_id
