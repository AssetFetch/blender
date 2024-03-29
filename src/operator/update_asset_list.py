import bpy,os,shutil,tempfile,uuid
from .. import http

class AF_OP_UpdateAssetList(bpy.types.Operator):
	"""Performs the initialization request to the provider and sets the provider settings, if requested."""
	
	bl_idname = "af.update_asset_list"
	bl_label = "Update Asset List"
	bl_options = {"REGISTER","UNDO"}

	thumbnail_icons : bpy.utils.previews.ImagePreviewCollection = None

	def draw(self,context):
		pass
		#layout = self.layout
		#layout.prop(self,'radius')

	def execute(self,context):
		af  = bpy.context.window_manager.af

		# Ensure that an empty temp directory is available
		thumbnail_temp_dir = os.path.join(tempfile.gettempdir(),"assetfetch-blender-thumbs")
		if os.path.exists(thumbnail_temp_dir):
			shutil.rmtree(thumbnail_temp_dir)
		os.makedirs(thumbnail_temp_dir,exist_ok=True)

		# Contact asset list endpoint
		response = af.current_provider_initialization.asset_list_query.to_http_query().execute()
		
		# Save assets in blender properties
		af.current_asset_list.configure(response.parsed)

		# Find the best thumbnail resolution and download it
		target_resolution = 128
		thumbnail_library_reset = False
		for asset in af.current_asset_list.assets:
			
			if asset.preview_image_thumbnail.is_set:

				# Remove old thumbnails from memory
				if not thumbnail_library_reset:
					if AF_OP_UpdateAssetList.thumbnail_icons:
						bpy.utils.previews.remove(AF_OP_UpdateAssetList.thumbnail_icons)
					AF_OP_UpdateAssetList.thumbnail_icons = bpy.utils.previews.new()
					thumbnail_library_reset = True

				# Start using the string index "0", if it is present
				# Otherwise use the first element in the uris array
				if "0" in asset.preview_image_thumbnail.uris:
					chosen_resolution = int(asset.preview_image_thumbnail.uris["0"].name)
				else:
					chosen_resolution = int(asset.preview_image_thumbnail.uris[0].name)
				current_best_deviation = abs(chosen_resolution-target_resolution)

				for thumb_res in asset.preview_image_thumbnail.uris.keys():
					thumb_res = int(thumb_res)
					if thumb_res > 0 and abs(chosen_resolution - thumb_res) < current_best_deviation:
						chosen_resolution = thumb_res
						current_best_deviation = abs(chosen_resolution-target_resolution)
				asset.preview_image_thumbnail.chosen_resolution = chosen_resolution

				# Perform the file download into temp directory
				asset.preview_image_thumbnail.temp_file_id = str(uuid.uuid4())
				thumb_file_location = os.path.join(thumbnail_temp_dir,asset.preview_image_thumbnail.temp_file_id)
				thumb_query = http.AF_HttpQuery(asset.preview_image_thumbnail.uris[str(asset.preview_image_thumbnail.chosen_resolution)],"get",None)
				thumb_query.execute_as_file(thumb_file_location)

				# Import the downloaded file
				AF_OP_UpdateAssetList.thumbnail_icons.load(
					name=asset.name,
					path=thumb_file_location,
					path_type='IMAGE'
				)
				asset.preview_image_thumbnail.icon_id = AF_OP_UpdateAssetList.thumbnail_icons[asset.name].icon_id

		return {'FINISHED'}
