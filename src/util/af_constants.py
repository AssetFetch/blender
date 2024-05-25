"""This module contains constants that represent concepts from AssetFetch."""

from enum import Enum


class AF_Colorspace(Enum):
	srgb = "srgb"
	linear = "linear"

	@staticmethod
	def property_items():
		return [("srgb", "sRGB", "sRGB"), ("linear", "linear", "linear")]

	def blender_value(self):
		if self.value == "linear":
			return "Non-Color"
		else:
			return "sRGB"


class AF_MaterialMap(Enum):
	albedo = "albedo"
	roughness = "roughness"
	metallic = "metallic"
	diffuse = "diffuse"
	glossiness = "glossiness"
	specular = "specular"
	height = "height"
	normal_plus_y = "normal+y"
	normal_minus_y = "normal-y"
	opacity = "opacity"
	ambient_occlusion = "ambient_occlusion"
	emission = "emission"

	@staticmethod
	def from_string_by_value(value: str):
		for material_map in AF_MaterialMap:
			if material_map.value == value:
				return material_map
		raise Exception("Invalid material map name.")

	@staticmethod
	def property_items():
		return [
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
		]
