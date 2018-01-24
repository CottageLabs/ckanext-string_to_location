FROM ubuntu:trusty
MAINTAINER Ryan Brooks <ryan@slatehorse.com>

# Set up the image to mirror how Travis Trusty image behaves
ENV PGVERSION=9.3

# A dirty hack to enable Postgres to start within this container
# Definitely only suitable for tests!
RUN sed -i "s/^exit 101$/exit 0/" /usr/sbin/policy-rc.d

# Allow Solr's Jetty to start
RUN printf "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nJAVA_HOME=$JAVA_HOME" | sudo tee /etc/default/jetty

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y sudo git python python-dev python-pip libpq-dev
RUN pip install ez_setup

# END Set up the image to mirror how Travis Trusty image behaves

RUN mkdir -p /var/testbed
ADD bin /var/testbed/bin

RUN /var/testbed/bin/travis-build-deps.bash

ADD . /var/testbed
RUN /var/testbed/bin/travis-build-plugin.bash

# Run with the local copy of the tests using:
# > docker build -t ckanext-string_to_location .
# > docker run --rm  -v .:/var/testbed ckanext-string_to_location
CMD /var/testbed/bin/travis-run.bash
