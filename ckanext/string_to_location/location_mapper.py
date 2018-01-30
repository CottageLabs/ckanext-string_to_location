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
       
        entities, errors = self._build_entities(self.table, self.column_name, self.is_name, source_entity_type)

        geojson_version = self._entities_to_geojson(entities, list(self.table.columns))

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
        

    def _entities_to_geojson(self, entities_array, properties):
            features = []
            for entity in entities_array:
                geometry = entity['entity'].geo_polygon.geometry
                feature_properties = {}
                for prop in properties:
                    feature_properties[prop] = entity['row'][prop]
                feature = Feature(properties= feature_properties, geometry=geometry)
                features.append(feature)

            return FeatureCollection(features)

    def _build_entities(self, table, column_name, is_name, source_entity_type):
        entities = []
        errors = []
        rows = 0
        for index, row in table.iterrows():
            rows += 1
            lookup_name = row[column_name]
            
            ons_entity = OnsEntityBuilder.build(lookup_name, source_entity_type, is_name=is_name)

            # FIXME: this shouldn't be an if statement
            if isinstance(ons_entity, NullOnsEntity):
                error_message = "Row:" + str(index) + ", " + lookup_name + " did not match."
                errors.append(error_message)
            else:
                entities.append({
                    'entity': ons_entity,
                    'row': row
                })

        return entities, errors

    