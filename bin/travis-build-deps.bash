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
echo 'oracle-java8-installer shared/accepted-oracle-license-v1-1 boolean true' | sudo debconf-set-selections
DEBIAN_FRONTEND=noninteractive sudo apt-get -y install oracle-java8-installer

echo "Installing Solr"
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
SOLR_CORE=ckan
sudo -u solr /opt/solr/bin/solr create -c ${SOLR_CORE}
sudo cp ckan/ckan/config/solr/schema.xml /var/solr/data/${SOLR_CORE}/conf/

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
cd -

echo "travis-build-deps.bash is done."
