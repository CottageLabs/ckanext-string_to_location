import geojson
from geojson import Feature
import os
import logging
from ons_entity_types import OnsEntityTypes


class OnsPolygonLookup:
    CODE_SUFFIX = 'cd'  # Lowercase in geojson

    lookup_filenames = {
        OnsEntityTypes.LOCAL_AUTHORITY_DISTRICT: [
                'Local_Authority_Districts_December_2009_Super_Generalised_Clipped_Boundaries_in_Great_Britain.geojson',
                'Local_Authority_Districts_December_2016_Super_Generalised_Clipped_Boundaries_in_the_UK.geojson',
                'Local_Authority_Districts_December_2017_Super_Generalised_Clipped_Boundaries_in_Great_Britain.geojson'
            ],
        OnsEntityTypes.COMMUNITY_SAFETY_PARTNERSHIP: ['community-safety-partnerships-december-2016-generalised-clipped-boundaries-in-england-and-wales.geojson'],
        OnsEntityTypes.POLICE_FORCE: None,
        OnsEntityTypes.NULL_ENTITY_TYPE: None
    }

    lookups = {}

    def __init__(self, entity_type, ons_code):
        self.entity_type = entity_type
        self.ons_code = ons_code

    def call(self):
        lookup_key = self.entity_type.value.lower() + self.CODE_SUFFIX

        if self.entity_type not in self.lookups:
            self.lookups[self.entity_type] = {}

            package_directory = os.path.dirname(os.path.abspath(__file__))
            filenames = self.lookup_filenames[self.entity_type]
            for filename in filenames:
                geojson_path = os.path.join(package_directory, 'data', 'polygons', filename)
                polygon_geojson = geojson.loads(open(geojson_path, "r").read())
                for mapping in polygon_geojson["features"]:
                    lookup_key = next((key for key in mapping["properties"] if key.startswith(self.entity_type.value.lower()) and key.endswith(self.CODE_SUFFIX)), None)

                    lookup_code = mapping["properties"][lookup_key]
                    self.lookups[self.entity_type][lookup_code] = mapping

        return self.lookups[self.entity_type].get(self.ons_code, None)
