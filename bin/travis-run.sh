#!/bin/sh -e

sudo service solr restart
sudo service postgresql restart

nosetests --ckan \
          --with-pylons=test.ini \
          --with-coverage \
          --cover-package=ckanext.string_to_location \
          --cover-inclusive \
          --cover-erase \
          --cover-tests
