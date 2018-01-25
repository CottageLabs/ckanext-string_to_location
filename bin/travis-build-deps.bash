#!/bin/bash
set -e

echo "This is travis-build-deps.bash..."

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install -y postgresql-$PGVERSION solr-jetty libcommons-fileupload-java:amd64=1.3-3

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/CottageLabs/ckan
cd ckan
# Don't take the latest branch, use this fixed one...
#export latest_ckan_release_branch=`git branch --all | grep remotes/origin/release-v | sort -r | sed 's/remotes\/origin\///g' | head -n 1`
export latest_ckan_release_branch=ckan-2.7.2-fixes
echo "CKAN branch: $latest_ckan_release_branch"
git checkout $latest_ckan_release_branch
python setup.py develop
pip install -r requirements.txt --allow-all-external
pip install -r dev-requirements.txt --allow-all-external
cd -

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

echo "SOLR config..."
cat <<- EOF | sudo tee -a /etc/default/jetty
NO_START=0
JETTY_HOST=127.0.0.1
JETTY_PORT=8983
JETTY_USER=root
JAVA_HOME=$JAVA_HOME
EOF

# Adding Files
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# sudo cp ${SCRIPT_DIR}/../solrconfig.xml /etc/solr/conf/

sudo cp ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml

# Solr is multicore for tests on ckan master, but it's easier to run tests on
# Travis single-core. See https://github.com/ckan/ckan/issues/2972
sed -i -e 's/solr_url.*/solr_url = http:\/\/127.0.0.1:8983\/solr/' ckan/test-core.ini

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
cd -

echo "travis-build-deps.bash is done."
