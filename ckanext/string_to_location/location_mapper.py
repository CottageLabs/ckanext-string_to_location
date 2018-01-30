from geojson import Feature, FeatureCollection

from ckanext.string_to_location.null_ons_entity import NullOnsEntity
from ckanext.string_to_location.ons_entity_builder import OnsEntityBuilder
from ckanext.string_to_location.ons_entity_types import OnsEntityTypes


class LocationMapper:

    COLUMN_TYPE_TO_ENTITY_TYPE = {
        "local_authority_district_name": OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT,
        "community_safety_partnership_name": OnsEntityTypes.COMMUNITY_SAFETY_PARTNERSHIP
    }

    def __init__(self, table, column_name, column_type, is_name):
        self.table = table
        self.column_name = column_name
        self.column_type = column_type
        self.is_name = is_name

    def map_and_build_geojson(self):

        source_entity_type = self.COLUMN_TYPE_TO_ENTITY_TYPE[self.column_type]

        entities, errors = self._build_entities(self.table, self.column_name, self.is_name, source_entity_type)

        geojson_version = self._entities_to_geojson(entities, list(self.table.columns))
        return geojson_version

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
