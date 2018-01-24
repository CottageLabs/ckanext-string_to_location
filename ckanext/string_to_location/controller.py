from StringIO import StringIO
import cgi
import os
import sys

from ckan.lib.base import render
import ckan.lib.base as base
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
from ckan.common import c
from ckan.common import config
import ckan.model

import ckan.logic as logic

from ckan.lib.navl.validators import not_empty

from ckan.controllers.package import PackageController

import ckan.lib.uploader as uploader


from ckanext.string_to_location.location_mapper_log_reader import LocationMapperLogReader
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter

from ckanext.string_to_location.ons_entity_types import OnsEntityTypes
from ckanext.string_to_location.null_ons_entity import NullOnsEntity
from ckanext.string_to_location.ons_entity_builder import OnsEntityBuilder
from ckanext.string_to_location.ons_code_mapper import OnsCodeMapper

import codecs
import csv
import geojson
from geojson import Feature, FeatureCollection
import pandas
import ast


class LocationMapperController(PackageController):

    def map_location(self, id, resource_id):
        context = None

        resource = toolkit.get_action('resource_show')(
            context, {'id': resource_id})

        print("This is the resource")
        print(resource)

        log_writer = LocationMapperLogWriter(resource_id)        
        
        resource_path = uploader.get_resource_uploader(resource).get_path(resource['id'])

        if 'location_column' in resource and 'location_type' in resource:
            column_name = resource['location_column']
            is_name = resource['location_type'].endswith('_name')
        elif 'location_column' in resource['_extras'] and 'location_type' in resource['_extras']:
            extras = ast.literal_eval(resource['_extras'])
            column_name = extras['location_column']
            is_name = extras['location_type'].endswith('_name')
        else:
            log_writer.error("The resource does not specify location columns", state="Something went wrong")
            return helpers.redirect_to(controller='ckanext.string_to_location.controller:LocationMapperController',
                                   action='resource_location_mapping_status', id=id, resource_id=resource_id)

        if "Local authority" in column_name:
            source_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT
        elif "Community Safety Partnership" in column_name:
            source_entity_type = OnsEntityTypes.COMMUNITY_SAFETY_PARTNERSHIP

        target_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT

        resource_contents = codecs.open(resource_path, 'rb', 'cp1257')

        table = pandas.read_csv(resource_contents)

        log_writer.info("Read file in")

        def get_geometry(name):
            entity = OnsEntityBuilder.build(name, source_entity_type, is_name=is_name)

            return entity.geo_polygon


        # Build the matches array

        # Attempt to map this from a CSP code into additional entities
        sources = []
        matches = []
        errors = []
        rows = 0
        for index, row in table.iterrows():
            rows += 1
            # For CSP lookup
            lookup_name = row[column_name]
            # First, build the ONS entity, so we can pass that around consistently
            # FIXME: this shouldn't be an if statement
            ons_entity = OnsEntityBuilder.build(lookup_name, source_entity_type, is_name=is_name)

            if not isinstance(ons_entity, NullOnsEntity):
                sources.append(ons_entity)
                row[source_entity_type.value + '_geojson'] = ons_entity.geo_polygon

            # Second, convert the entity into a LAD (builds a new object, of course)
            local_authority_district = OnsCodeMapper(ons_entity, target_entity_type).call()

            if isinstance(local_authority_district, NullOnsEntity):
                error_message = "Row:" + str(index) + ", " + lookup_name + " did not match."
                errors.append(error_message)
            else:
                matches.append({
                    'entity': local_authority_district,
                    'row': row
                })


        def matches_to_geojson(match_array, properties):
            features = []
            for match in match_array:
                geometry = match['entity'].geo_polygon.geometry
                feature_properties = {}
                for prop in properties:
                    feature_properties[prop] = match['row'][prop]
                feature = Feature(properties= feature_properties, geometry=geometry)
                features.append(feature)

            return FeatureCollection(features)

        geojson_version = matches_to_geojson(matches, list(table.columns))

        output_buffer = StringIO()
        geojson.dump(geojson_version, output_buffer, ignore_nan=True)

        #
        # Summary info
        #

        # match_count = len(matches)
        # error_count = len(errors)

        # matches_with_polygons = sum(1 for match in matches if match['entity'].geo_polygon is not None)

        # print("========================")
        # print("Summary:")
        # print("")
        # print(f"    {rows} rows in source file")
        # print(f"    {match_count} {target_entity_type.value} mapped")
        # print(f"    {error_count} errors")
        # print("")
        # print(f"    {matches_with_polygons} matches with polygons")

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

        logic.action.create.resource_create(
            {"model": ckan.model, "user": c.userobj.name}, data_dict)

        log_writer.info("Added new resource to dataset " \
                       + config.get('ckan.site_url')  \
                       + helpers.url_for(controller='package', 
                                        action='resource_read', 
                                        id=resource['package_id'], 
                                        resource_id=resource['id']), 
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

        return base.render('custom/resource_location_mapping_status.html',
                           extra_vars={'status': status})
