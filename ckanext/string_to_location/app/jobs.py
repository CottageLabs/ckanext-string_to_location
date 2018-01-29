import ckanserviceprovider.job as job
import ckanserviceprovider.util as util
from ckanserviceprovider import web

from ckan.common import c
import ckan.model
import ckan.logic as logic
import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit

import cgi
import os
import sys
import codecs
import csv
import geojson
import pandas
import ast

from location_mapper import LocationMapper
from location_mapper_log_reader import LocationMapperLogReader
from location_mapper_log_writer import LocationMapperLogWriter

def upload_augmented_resource(self, resource, output_buffer):
    upload = cgi.FieldStorage()
    # FIXME: replace with source filename + modified extension
    upload.filename = 'mapped_output.geojson'
    upload.file = output_buffer

    data_dict = {
        "package_id": resource['package_id'],
        "name": "Augmented " + resource['name'],
        "description": "Geo-mapped representation of " + resource['name'],
        "format": "application/geo+json",
        "upload": upload
    }

    new_resource = logic.action.create.resource_create(
        {"model": ckan.model, "user": c.userobj.name}, data_dict)

    return new_resource

@job.async
def map_location(resource_id):
    resource = toolkit.get_action('resource_show')(
            context, {'id': resource_id})
    log_writer = LocationMapperLogWriter(resource['id'])

    resource_path = uploader.get_resource_uploader(resource).get_path(resource['id'])
    resource_contents = codecs.open(resource_path, 'rb', 'cp1257')

    table = pandas.read_csv(resource_contents)

    log_writer.info("Read " + resource['name'] + " in")

    output_buffer = LocationMapper(table, column_name, is_name).map_location()

    new_resource = upload_augmented_resource(resource, output_buffer)

    log_writer.info("Added new resource to dataset " \
                   + config.get('ckan.site_url')  \
                   + helpers.url_for(controller='package', 
                                    action='resource_read', 
                                    id=new_resource['package_id'], 
                                    resource_id=new_resource['id']), 
                   state="complete")

