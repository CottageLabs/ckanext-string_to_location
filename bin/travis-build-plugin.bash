echo "This is travis-build-deps.bash..."

echo "Installing ckanext-string_to_location and its requirements..."
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt --upgrade

echo "travis-build-plugin.bash is done."