# Download the required packages into the src/lib directory
pip install --target ./src/lib/ -r ./requirements.txt

# Download the latest json schema version for AssetFetch
# Change the -b parameter to use a different branch/tag
mkdir ./tmp
git -C ./tmp/ clone -b '0.3' --single-branch https://github.com/AssetFetch/spec.git 
cp -r ./tmp/spec/json-schema/ ./src/
rm -rf ./tmp