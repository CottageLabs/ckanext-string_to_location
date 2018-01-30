import cgi
import os
import sys
import codecs
import csv
import geojson
import logging
import pandas

from geojson import Feature, FeatureCollection
from StringIO import StringIO

import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
import ckan.logic as logic
from ckan.common import config

import ckan.lib.helpers as helpers
import ckan.model

from ckanext.string_to_location.location_mapper_log_reader import LocationMapperLogReader
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter

from ckanext.string_to_location.ons_entity_types import OnsEntityTypes
from ckanext.string_to_location.null_ons_entity import NullOnsEntity
from ckanext.string_to_location.ons_entity_builder import OnsEntityBuilder
from ckanext.string_to_location.ons_code_mapper import OnsCodeMapper

# FIXME comments EVIL HACK
def map_location_async(resource_id, username):
    '''
    Background job
    '''

    context = None
    resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

    log_writer = LocationMapperLogWriter(resource['id'])

    #
    # Validation
    # TODO: This is carried out in the controller, so we need to either:
    #   1. Trust that the input is good...
    #   2. Refactor this into a common place to keep it DRY
    #
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

    if column_name is None:
        log_writer.error("The resource does not specify location columns", state="Something went wrong")


    resource_path = uploader.get_resource_uploader(resource).get_path(resource['id'])
    resource_contents = codecs.open(resource_path, 'rb', 'cp1257')

    table = pandas.read_csv(resource_contents)

    log_writer.info("Loaded contents of " + resource['name'])

    output_buffer = LocationMapper(table, column_name, column_type, is_name).map_location()

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
        {"model": ckan.model, "ignore_auth": True, "user": username}, data_dict)

    # Update the user-facing log
    log_writer.info("Added new resource to dataset " \
                   + config.get('ckan.site_url')  \
                   + helpers.url_for(controller='package',
                                    action='resource_read',
                                    id=new_resource['package_id'],
                                    resource_id=new_resource['id']),
                   state="complete")

class LocationMapper:

    COLUMN_TYPE_TO_ENTITY_TYPE = {
        "local_authority_district_name" : OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT,
        "community_safety_partnership_name" : OnsEntityTypes.COMMUNITY_SAFETY_PARTNERSHIP
    }

    def __init__(self, table, column_name, column_type, is_name):
        self.table = table
        self.column_name = column_name
        self.column_type = column_type
        self.is_name = is_name

    def map_location(self):

        source_entity_type = self.COLUMN_TYPE_TO_ENTITY_TYPE[self.column_type]
        target_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT

        matches, errors = self._build_matches(self.table, self.column_name, self.is_name, source_entity_type, target_entity_type)

        geojson_version = self._matches_to_geojson(matches, list(self.table.columns))

        output_buffer = StringIO()
        geojson.dump(geojson_version, output_buffer, ignore_nan=True)

        return output_buffer

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


    def _matches_to_geojson(self, match_array, properties):
            features = []
            for match in match_array:
                geometry = match['entity'].geo_polygon.geometry
                feature_properties = {}
                for prop in properties:
                    feature_properties[prop] = match['row'][prop]
                feature = Feature(properties= feature_properties, geometry=geometry)
                features.append(feature)

            return FeatureCollection(features)

    def _build_matches(self, table, column_name, is_name, source_entity_type, target_entity_type):
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

        return matches, errors


