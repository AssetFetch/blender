# AssetFetch for Blender

This addon is a client for the [AssetFetch protocol](https://assetfetch.org), an open system for 3D asset discovery and automated imports.

![image](https://github.com/struffel/assetfetch-blender/assets/31403260/6f218e1a-2de1-4054-97f0-99655d513dad)

# Installation

**A user-friendly installation via ZIP file is not yet available, but it will be provided along with the first actual release in the near future.**
Until then the addon can only be installed using the development setup, outlined below.

## Development Setup

This is the setup for developing the addon.

1. Create a symlink in your filesystem that connects the `/src` folder in this repository with blender's addon directory, for example on Windows this would be `C:\Users\<User>\AppData\Roaming\Blender Foundation\Blender\4.0\scripts\addons\src`.
2. Download the required python-dependencies:
```bash
# Make sure that you are in the root of this repository (same directory as this readme file)
# Download the required packages into the src/lib directory
pip install --target ./src/lib/ -r ./requirements.txt
```
3. Download the JSON-Schema for AssetFetch
```bash
# Download the latest json schema version for AssetFetch
# Change the -b parameter to use a different branch/tag
mkdir ./tmp
git -C ./tmp/ clone -b '0.2' --single-branch https://github.com/AssetFetch/spec.git 
cp -r ./tmp/spec/json-schema/ ./src/
rm -rf ./tmp
```
4. I recommend developing in VS Code with the [Blender Development Extension by Jacques Lucke](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)

## Code overview

The addon is split into multiple modules:

- `operator` contains all the bpy operators, meaning all the distinct actions this addon can perform.
- `property` contains all the bpy properties that are used to store and handle the incoming data from the provider. AF stores all its data in  `bpy.context.window_manager.af`.
- `ui` contains the code for the individual panels, all of which are in the `VIEW_3D` section (meaning the window that you get by opening the right-side panel in the 3D view).
- `util` is for miscellaneous functionality, currently that is only the http module that's being used to make all HTTP requests and validate them against the JSON schema.

Every module's `__init__.py` imports all relevant classes and stores them in a `registration_targets` array from where the `register()` and `unregister()` functions read them when the addon is (un)loaded inside Blender.

The global `__init__.py` for the entire addon does the same pattern again by loading the registration functions from all the other modules.

Required dependencies are loaded from the `/src/lib` directory.
