from enum import Enum
import bpy
import bpy_extras.image_utils
from . import af_constants

def get_or_create_material(material_name:str,af_namespace:str):
		
	for existing_material in bpy.data.materials:
		if ("af_name" in existing_material) and ("af_namespace" in existing_material):
			if existing_material['af_name'] == material_name and existing_material['af_namespace'] == af_namespace:
				return existing_material

	new_material= bpy.data.materials.new(name=material_name)
	new_material.use_nodes = True

	# Add principled bsdf and tex coord
	new_material.node_tree.nodes.clear()
	output = new_material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
	output.location.x = 1600
	output.name = "OUTPUT"
	bsdf_shader = new_material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
	bsdf_shader.location.x = 1200
	bsdf_shader.name = "BSDF"
	tex_coord = new_material.node_tree.nodes.new(type='ShaderNodeTexCoord')
	tex_coord.location.x = -800
	tex_coord.name = "TEX_COORD"

	# Basic links
	new_material.node_tree.links.new(bsdf_shader.outputs['BSDF'],output.inputs['Surface'])

	# Mark as AssetFetch-managed
	new_material['af_namespace'] = af_namespace
	new_material['af_name'] = material_name

	return new_material

def count_image_nodes(shader_tree:bpy.types.NodeTree):
	"""Counts how many image (TEX_IMAGE) nodes are in a given node tree."""
	image_node_count = 0
	for node in shader_tree.nodes:
		if node.type == 'TEX_IMAGE':
			image_node_count += 1
	return image_node_count

def add_map_to_material(target_material:bpy.types.Material,colorspace:af_constants.AF_Colorspace,map:af_constants.AF_MaterialMap,image_target_path:str):

	# Import the file from local_path into blender
	image = bpy_extras.image_utils.load_image(imagepath=image_target_path)

	# Set color space
	image.colorspace_settings.name = colorspace.blender_value()

	# Assign the map to the material
	image_node = target_material.node_tree.nodes.new(type='ShaderNodeTexImage')
	image_node.image = image

	# Position the image node and related nodes based on how many image nodes are already in the material
	current_vertical_node_position = ( count_image_nodes(target_material.node_tree) -1 ) * -300
	image_node.location.y =  current_vertical_node_position

	# Connect
	target_material.node_tree.links.new(target_material.node_tree.nodes['TEX_COORD'].outputs['UV'],image_node.inputs['Vector'])
	
	# Make connection into bsdf shader
 
	# Helper variables
	image_color_out = image_node.outputs['Color']
	bsdf_inputs = target_material.node_tree.nodes['BSDF'].inputs

	# Color Map
	if map in [af_constants.AF_MaterialMap.albedo,af_constants.AF_MaterialMap.diffuse]:
		color_image_node = target_material.node_tree.links.new(image_color_out,bsdf_inputs['Base Color'])

	# Normal Map
	if map in [af_constants.AF_MaterialMap.normal_plus_y,af_constants.AF_MaterialMap.normal_minus_y]:
		normal_map_node = target_material.node_tree.nodes.new(type="ShaderNodeNormalMap")
		normal_map_node.location.x = 800
		normal_map_node.location.y = current_vertical_node_position
		target_material.node_tree.links.new(normal_map_node.outputs['Normal'],target_material.node_tree.nodes['BSDF'].inputs['Normal'])
	
	if map == af_constants.AF_MaterialMap.normal_plus_y:
		target_material.node_tree.links.new(image_node.outputs['Color'],normal_map_node.inputs['Color'])

	if map == af_constants.AF_MaterialMap.normal_minus_y:
		# Green channel must be inverted
		# Separate Color
		separate_color_node = target_material.node_tree.nodes.new(type="ShaderNodeSeparateColor")
		separate_color_node.location.y = current_vertical_node_position
		separate_color_node.location.x = 250
		target_material.node_tree.links.new(image_node.outputs['Color'],separate_color_node.inputs['Color'])
		# Invert Green
		invert_normal_y_node = target_material.node_tree.nodes.new(type="ShaderNodeInvert")
		invert_normal_y_node.location.y = current_vertical_node_position
		invert_normal_y_node.location.x = 400
		target_material.node_tree.links.new(separate_color_node.outputs['Green'],invert_normal_y_node.inputs['Color'])
		# Combine again
		combine_color_node = target_material.node_tree.nodes.new(type="ShaderNodeCombineColor")
		combine_color_node.location.y = current_vertical_node_position
		combine_color_node.location.x = 550
		target_material.node_tree.links.new(invert_normal_y_node.outputs['Color'],combine_color_node.inputs['Green'])
		target_material.node_tree.links.new(separate_color_node.outputs['Red'],combine_color_node.inputs['Red'])
		target_material.node_tree.links.new(separate_color_node.outputs['Blue'],combine_color_node.inputs['Blue'])
		# Connect to normal node
		target_material.node_tree.links.new(combine_color_node.outputs['Color'],normal_map_node.inputs['Color'])

	# Roughness Map
	if map == af_constants.AF_MaterialMap.roughness:
		target_material.node_tree.links.new(image_color_out,bsdf_inputs['Roughness'])

	# Glossiness
	if map == af_constants.AF_MaterialMap.glossiness:
		# Map needs to be inverted
		invert_roughness_node = target_material.node_tree.nodes.new(type="ShaderNodeInvert")
		invert_roughness_node.location.y = current_vertical_node_position
		invert_roughness_node.location.x = 400
		target_material.node_tree.links.new(image_color_out,invert_roughness_node.inputs['Color'])
		target_material.node_tree.links.new(invert_roughness_node.outputs['Color'],bsdf_inputs['Roughness'])

	# Metalness Map
	if map == af_constants.AF_MaterialMap.metallic:
		target_material.node_tree.links.new(image_color_out,bsdf_inputs['Metallic'])

	# Height
	if map == af_constants.AF_MaterialMap.height:
		displacement_node = target_material.node_tree.nodes.new("ShaderNodeDisplacement")
		displacement_node.location.x = 400
		displacement_node.location.y = current_vertical_node_position
		target_material.node_tree.links.new(image_color_out,displacement_node.inputs['Height'])
		target_material.node_tree.links.new(displacement_node.outputs['Displacement'],target_material.node_tree.nodes['OUTPUT'].inputs['Displacement'])
	
	# Opacity
	if map == af_constants.AF_MaterialMap.opacity:
		target_material.node_tree.links.new(image_color_out,bsdf_inputs['Alpha'])

	# Emission
	if map == af_constants.AF_MaterialMap.emission:
		target_material.node_tree.links.new(image_color_out,bsdf_inputs['Emission Color'])