from ckan.lib.base import render
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
from ckan.controllers.package import PackageController

import ckan.lib.helpers as helpers
import ckan.lib.uploader as uploader
from ckan.lib.navl.validators import not_empty
from ckan.common import c
from ckan.common import config
import ckan.model
import ckan.logic as logic

from ckanext.string_to_location.location_mapper import LocationMapper
from ckanext.string_to_location.location_mapper_log_reader import LocationMapperLogReader
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter

import cgi
import os
import sys
import codecs
import csv
import geojson
import pandas
import ast


class LocationMapperController(PackageController):

    def map_location(self, id, resource_id):
        context = None
        resource = toolkit.get_action('resource_show')(
            context, {'id': resource_id})
        log_writer = LocationMapperLogWriter(resource['id']) 

        column_name, column_type, is_name = self._set_column_name_and_type(resource)

        if column_name is None:
            log_writer.error("The resource does not specify location columns", state="Something went wrong")
            return helpers.redirect_to(controller='ckanext.string_to_location.controller:LocationMapperController',
                                   action='resource_location_mapping_status', id=id, resource_id=resource_id)

        resource_path = uploader.get_resource_uploader(resource).get_path(resource['id'])
        resource_contents = codecs.open(resource_path, 'rb', 'cp1257')

        table = pandas.read_csv(resource_contents)

        log_writer.info("Read " + resource['name'] + " in")

        output_buffer = LocationMapper(table, column_name, column_type, is_name).map_location()

        new_resource = self._upload_augmented_resource(resource, output_buffer)

        log_writer.info("Added new resource to dataset " \
                       + config.get('ckan.site_url')  \
                       + helpers.url_for(controller='package', 
                                        action='resource_read', 
                                        id=new_resource['package_id'], 
                                        resource_id=new_resource['id']), 
                       state="complete")

        return helpers.redirect_to(controller='ckanext.string_to_location.controller:LocationMapperController',
                                   action='resource_location_mapping_status', id=id, resource_id=resource_id)

    def resource_location_mapping_status(self, id, resource_id):

        context = None

        try:
            toolkit.c.pkg_dict = toolkit.get_action('package_show')(
                context, {'id': id}
            )
            toolkit.c.resource = toolkit.get_action('resource_show')(
                context, {'id': resource_id}
            )
        except (logic.NotFound, logic.NotAuthorized):
            base.abort(404, _('Resource not found'))

        log_reader = LocationMapperLogReader(resource_id)

        status = log_reader.get_status()

        return render('custom/resource_location_mapping_status.html',
                           extra_vars={'status': status})

    def _set_column_name_and_type(self, resource):

        if 'location_column' in resource and 'location_type' in resource:
            column_name = resource['location_column']
            column_type=resource['location_type']
            is_name = resource['location_type'].endswith('_name')
        elif 'location_column' in resource['_extras'] and 'location_type' in resource['_extras']:
            extras = ast.literal_eval(resource['_extras'])
            column_name = extras['location_column']
            column_type=extras['location_type']
            is_name = extras['location_type'].endswith('_name')
        else:
            column_name = None
            column_type = None
            is_name = None

        return column_name, column_type, is_name

    def _upload_augmented_resource(self, resource, output_buffer):
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
