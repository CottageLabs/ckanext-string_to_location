#!/bin/sh -e

cat <<- EOF | sudo tee /etc/default/jetty
NO_START=0
JETTY_HOST=127.0.0.1
JETTY_PORT=8983
JETTY_USER=root
JAVA_HOME=/usr/lib/jvm/default-java
EOF
sudo cp ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml
sudo service jetty restart
sudo service postgresql restart

nosetests --ckan \
          --with-pylons=test.ini \
          --with-coverage \
          --cover-package=ckanext.string_to_location \
          --cover-inclusive \
          --cover-erase \
          --cover-tests
