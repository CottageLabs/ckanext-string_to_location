from StringIO import StringIO
import cgi
import os
import sys
import logging
from ckan.lib.base import request
from ckan.lib.base import model
from ckan.lib.base import render
import ckan.lib.base as base
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
from ckan.common import c
import ckan.model

import ckan.logic as logic

from ckan.lib.navl.validators import not_empty

from ckan.controllers.package import PackageController

from ckanext.radar_dms.location_mapper_log_reader import LocationMapperLogReader
from ckanext.radar_dms.location_mapper_log_writer import LocationMapperLogWriter

from ckanext.radar_dms.ons_entity_types import OnsEntityTypes
from ckanext.radar_dms.null_ons_entity import NullOnsEntity
from ckanext.radar_dms.ons_entity_builder import OnsEntityBuilder
from ckanext.radar_dms.ons_code_mapper import OnsCodeMapper

import codecs
import csv
import geojson
from geojson import Feature, FeatureCollection
import pandas


class LocationMapperController(PackageController):

    def map_location(self, id, resource_id):
        context = None

        resource = toolkit.get_action('resource_show')(
            context, {'id': resource_id})

        log_writer = LocationMapperLogWriter(resource_id)

        source_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT
        target_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT
        resource_path = '/var/lib/ckan/resources/' + \
            resource['id'][:3] + '/' + \
            resource['id'][3:6] + '/' + resource['id'][6:]
        column_name = 'Local authority'
        is_name = True

        resource_contents = codecs.open(resource_path, 'rb', 'cp1257')

        table = pandas.read_csv(resource_contents)

        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
        log_writer.info("Read file in")

        def get_geometry(name):
            entity = OnsEntityBuilder.build(name, source_entity_type, is_name=is_name)

            return entity.geo_polygon

        # Augment the data frame with source polygon
        table[source_entity_type.value + '_geometry'] = table.apply(lambda row: get_geometry(row[column_name]), axis=1)

        csv_buffer = StringIO()
        table.to_csv(csv_buffer, sep='\t')

        upload = cgi.FieldStorage()
        # FIXME: hard-coded filename
        upload.filename = 'test.tsv'
        upload.file = csv_buffer

        data_dict = {
            "package_id": resource['package_id'],
            "name": "Augmented " + resource['name'],
            "description": "Augmented file containing local authority polygons",
            "format": "text/tsv",
            "upload": upload
        }

        logic.action.create.resource_create(
            {"model": ckan.model, "user": c.userobj.name}, data_dict)

        log_writer.info("Added new resource to dataset", state="complete")

        return helpers.redirect_to(controller='ckanext.radar_dms.controller:LocationMapperController',
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

        return base.render('custom/resource_location_mapping_status.html',
                           extra_vars={'status': status})
