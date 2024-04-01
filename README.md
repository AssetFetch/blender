# assetfetch-blender
An AssetFetch client for Blender.

## Development Setup
```
# Make sure that you are in the root of this directory (same directory as this readme file)

# Download the required packages into the src/lib directory
pip install --target ./src/lib/ -r ./requirements.txt

# Download the latest json schema version for AssetFetch
mkdir ./tmp
git -C ./tmp/ clone -b main --single-branch https://github.com/AssetFetch/spec.git 
cp -r ./tmp/spec/json-schema/ ./src/
rm -rf ./tmp
```