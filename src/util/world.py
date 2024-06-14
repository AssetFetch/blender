import bpy
import bpy_extras.image_utils
from . import af_constants


def create_world(world_name: str, hdr_image_path: str, af_namespace: str):
	"""Returns a Blender World (existing or newly created) with the given name, AF Namespace, and sets up HDRI image."""

	# Create a new world
	new_world = bpy.data.worlds.new(name=world_name)
	new_world.use_nodes = True

	# Clear existing nodes
	new_world.node_tree.nodes.clear()

	# Add output node
	output = new_world.node_tree.nodes.new(type='ShaderNodeOutputWorld')
	output.location.x = 600
	output.name = "OUTPUT"

	# Add background shader
	background_shader = new_world.node_tree.nodes.new(type='ShaderNodeBackground')
	background_shader.location.x = 400
	background_shader.name = "BACKGROUND"

	# Add environment texture node
	env_texture = new_world.node_tree.nodes.new(type='ShaderNodeTexEnvironment')
	env_texture.location.x = 100
	env_texture.name = "ENV_TEXTURE"

	# Add mapping node for rotation
	mapping = new_world.node_tree.nodes.new(type='ShaderNodeMapping')
	mapping.location.x = -100
	mapping.name = "MAPPING"

	# Add texture coordinate node
	tex_coord = new_world.node_tree.nodes.new(type='ShaderNodeTexCoord')
	tex_coord.location.x = -300
	tex_coord.name = "TEX_COORD"

	# Basic links
	new_world.node_tree.links.new(env_texture.outputs['Color'], background_shader.inputs['Color'])
	new_world.node_tree.links.new(background_shader.outputs['Background'], output.inputs['Surface'])
	new_world.node_tree.links.new(mapping.outputs['Vector'], env_texture.inputs['Vector'])
	new_world.node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])

	# Load HDRI image

	hdr_image = bpy_extras.image_utils.load_image(hdr_image_path)
	if hdr_image:
		env_texture.image = hdr_image
	else:
		raise Exception(f"Failed to load HDR image from {hdr_image_path}")

	# Mark as AssetFetch-managed
	new_world['af_namespace'] = af_namespace
	new_world['af_name'] = world_name

	return new_world
