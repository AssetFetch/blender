$BLENDER_VERSION = "5.0"
& "$ENV:ProgramFiles\Blender Foundation\Blender $BLENDER_VERSION\blender.exe" --command extension build --source-dir $PSScriptRoot/src --verbose
& "$ENV:ProgramFiles\Blender Foundation\Blender $BLENDER_VERSION\blender.exe" --command extension server-generate --repo-dir $PSScriptRoot