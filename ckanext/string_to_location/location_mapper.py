import cgi
import os
import sys
import codecs
import csv
import geojson

from geojson import Feature, FeatureCollection
from StringIO import StringIO

from ckanext.string_to_location.ons_entity_types import OnsEntityTypes
from ckanext.string_to_location.null_ons_entity import NullOnsEntity
from ckanext.string_to_location.ons_entity_builder import OnsEntityBuilder
from ckanext.string_to_location.ons_code_mapper import OnsCodeMapper


class LocationMapper:

    COLUMN_TO_ENTITY = {
        "Local Authority District" : OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT,
        "Local authority" : OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT,
        "Community Safety Partnership" : OnsEntityTypes.COMMUNITY_SAFETY_PARTNERSHIP
    }

    def __init__(self, table, column_name, is_name):
        self.table = table
        self.column_name = column_name
        self.is_name = is_name

    def map_location(self):
                       
        source_entity_type = self.COLUMN_TO_ENTITY[self.column_name]
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

    