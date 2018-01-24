FROM ubuntu:trusty
MAINTAINER Ryan Brooks <ryan@slatehorse.com>

# Set up the image to mirror how Travis Trusty image behaves
ENV PGVERSION=9.3

# A dirty hack to enable Postgres to start within this container
# Definitely only suitable for tests!
RUN sed -i "s/^exit 101$/exit 0/" /usr/sbin/policy-rc.d

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y sudo git python python-dev python-pip libpq-dev
RUN pip install ez_setup

# END Set up the image to mirror how Travis Trusty image behaves

ENV PLUGIN_DIRECTORY=/var/testbed
WORKDIR $PLUGIN_DIRECTORY

RUN mkdir -p $PLUGIN_DIRECTORY
ADD bin ./bin

RUN ./bin/travis-build-deps.bash



ADD . .
RUN ./bin/travis-build-plugin.bash

# Run with the local copy of the tests using:
# > docker build -t ckanext-string_to_location .
# > docker run --rm  -v .:/var/testbed ckanext-string_to_location
CMD ./bin/travis-run.sh
