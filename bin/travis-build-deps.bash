#!/bin/bash
set -e

echo "This is travis-build-deps.bash..."

echo "Installing the packages that CKAN requires..."
# lsof is necessary for Solr
sudo apt-get update -qq
sudo apt-get install -y postgresql-$PGVERSION libcommons-fileupload-java:amd64=1.3-3 lsof

# Install Java/Solr
# sudo apt-get install -y openjdk-8-jre
sudo apt-get install -y software-properties-common python-software-properties
add-apt-repository -y ppa:webupd8team/java
sudo apt-get update -qq
echo 'oracle-java8-installer shared/accepted-oracle-license-v1-1 boolean true' | debconf-set-selections
DEBIAN_FRONTEND=noninteractive apt-get -y install oracle-java8-installer

cd /tmp
curl -s --remote-name-all http://apache.mirror.anlx.net/lucene/solr/6.6.2/solr-6.6.2.tgz
tar xzf solr-6.6.2.tgz solr-6.6.2/bin/install_solr_service.sh --strip-components=2
sudo ./install_solr_service.sh solr-6.6.2.tgz
cd -

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

# Adding Files
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# sudo cp ${SCRIPT_DIR}/../solrconfig.xml /etc/solr/conf/

SOLR_CORE=ckan
SOLR_USER=root
SOLR_PATH=/var/solr/data/$SOLR_CORE

# # Create Directories
# mkdir -p ${SOLR_PATH}/conf
# mkdir -p ${SOLR_PATH}/data


sudo -u solr -c "/opt/solr/bin/solr create -c ${SOLR_CORE}"

# Adding Files
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# cp  ${SCRIPT_DIR}/solrconfig.xml $SOLR_PATH/conf/

sudo cp ckan/ckan/config/solr/schema.xml $SOLR_PATH/conf/

# Create Core.properties
# echo name=$SOLR_CORE > $SOLR_PATH/core.properties

# Giving ownership to Solr
# chown -R $SOLR_USER:$SOLR_USER $SOLR_PATH

# Solr is multicore for tests on ckan master, but it's easier to run tests on
# Travis single-core. See https://github.com/ckan/ckan/issues/2972
# sed -i -e 's/solr_url.*/solr_url = http:\/\/127.0.0.1:8983\/solr/' ckan/test-core.ini

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
cd -

echo "travis-build-deps.bash is done."
