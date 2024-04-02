# Download the required packages into the src/lib directory
pip install --target ./src/lib/ -r ./requirements.txt

# Download the latest json schema version for AssetFetch
New-Item -ItemType Directory -Force -Path ./tmp
git -C ./tmp/ clone -b main --single-branch https://github.com/AssetFetch/spec.git 
Copy-Item -Recurse -Force -Path ./tmp/spec/json-schema/ -Destination ./src/
Remove-Item -Force -Recurse -Path ./tmp