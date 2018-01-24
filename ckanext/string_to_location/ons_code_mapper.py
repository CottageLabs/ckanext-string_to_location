import geojson
import ckan.logic as logic

from ons_entity_builder import OnsEntityBuilder


class OnsCodeMapper:
    """Maps between Local Authority Districts, Community Safetey Partnerships, and Police Forces.

    Uses ONS codes to map between different schemes. Valid schemes are:
        - 'LAD16NM': Local Authority name
        - 'LAD16CD': Local Authority code
        - 'CSP16NM': Community Safety Partnership name
        - 'CSP16CD': Community Safety Partnership code
        - 'PFA16NM': Police Force name
        - 'PFA16CD': Police Force code

    The `OnsCodeLookup` is useful to look up entities from names and codes.

    Note: As of 2018-01-16 only codes included in the December 2016 release are mapped.
    TODO: Include previous releases of the mapping.

    Note:
        This class currently takes a naive approach to mapping, and returns the first valid match.
        Some entities contain multiple instances of other entities (e.g. a Unitary Authority often
        contains many Local Authority Districts), but this is not reflected in the response (yet).

    """

    package_directory = os.path.dirname(os.path.abspath(__file__))
    la_csp_pf_mapping_path = os.path.join(package_directory, 'data', 'lookups', 'Local_Authority_District_to_Community_Safety_Partnerships_to_Police_Force_Areas_December_2016_Lookup_in_England_and_Wales.geojson')

    la_csp_pf_mapping = geojson.loads(open(la_csp_pf_mapping_path, "r").read())

    def __init__(self, ons_entity, target_entity_type):
        self.ons_entity = ons_entity
        self.target_entity_type = target_entity_type

    def call(self):
        key = self.ons_entity.ons_code
        from_scheme = self.ons_entity.entity_type.value + 'CD'
        to_scheme = self.target_entity_type.value + 'CD'
        match = next((x for x in self.la_csp_pf_mapping['features'] if x.get(
            "properties", {}).get(from_scheme, '') == key), {})
        target_code = match.get('properties', {}).get(to_scheme, None)
        return OnsEntityBuilder.from_code(target_code, self.target_entity_type)
