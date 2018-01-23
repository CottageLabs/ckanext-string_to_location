#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import csv
import geojson
from geojson import Feature, FeatureCollection
import pandas


from ons_entity_types import OnsEntityTypes
from null_ons_entity import NullOnsEntity
from ons_entity_builder import OnsEntityBuilder
from ons_code_mapper import OnsCodeMapper

#
# TODO: refactor everything below into classes (pretty much)
# TODO: output matched names & codes as additional columns
#

source_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT
target_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT
resource_path = 'data/Maintained_schools_and_academies_inspection_outcomes_as_at_31_December_2016_schools_inspection_data_September_2016_and_31_December_2016.csv'
column_name = 'Local authority'
is_name = True


# resource_path = 'data/rec-crime-csp-file2.csv'
# column_name = 'ONS Code'
# source_entity_type = OnsEntityTypes.COMMUNITY_SAFETY_PARTNERSHIP
# target_entity_type = OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT
# is_name = False

# Load the resource
resource_contents = codecs.open(resource_path, 'rb', 'cp1257')
table = pandas.read_csv(resource_contents)

#
# Augment the data frame with source polygon
# table[source_entity_type.value + '_geometry'] = table.apply (lambda row: OnsEntityBuilder.build(row[column_name], source_entity_type, is_name=is_name).geo_polygon,axis=1)
# table.to_csv(resource_path+'_output.tsv',sep='\t')

#
# Write geojson

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
        error_message = f"Row: {index}, {lookup_name} did not match."
        errors.append(error_message)
    else:
        matches.append(local_authority_district)
        # print(f"✅  {lookup_name} matched {local_authority_district.ons_code}")

#
# TODO: amalgamate rows for the same entity as row properties
# def df_to_geojson(df, properties):
#     features = []
#     for _, row in df.iterrows():
#         feature_properties = {}
#         for prop in properties:
#             feature_properties[prop] = row[prop]
#         feature = Feature(properties= feature_properties, geometry=ons_entity.geo_polygon)
#         features.append(feature)

#     return FeatureCollection(features)


# geojson_version = df_to_geojson(table, list(table.columns))

# with open(resource_path+'.geojson', 'w') as outfile:
#     geojson.dump(geojson_version, outfile, allow_nan=True)

#
# Summary info
#

source_count = len(sources)
match_count = len(matches)
error_count = len(errors)

sources_with_polygons = sum(1 for entity in sources if entity.geo_polygon is not None)
matches_with_polygons = sum(1 for entity in matches if entity.geo_polygon is not None)

print("========================")
print("Summary:")
print("")
print(f"    {rows} rows in source file")
print(f"    {source_count} {source_entity_type.value} matched")
print(f"    {match_count} {target_entity_type.value} mapped")
print(f"    {error_count} errors")
print("")
print(f"    {sources_with_polygons} sources with polygons")
print(f"    {matches_with_polygons} matches with polygons")
