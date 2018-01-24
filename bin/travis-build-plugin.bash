echo "This is travis-build-deps.bash..."

echo "Installing ckanext-string_to_location and its requirements..."
python setup.py develop
pip install -r dev-requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "travis-build-plugin.bash is done."