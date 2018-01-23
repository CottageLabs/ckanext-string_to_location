from ons_entity import OnsEntity
from ons_entity_types import OnsEntityTypes


class NullOnsEntity(OnsEntity):
    def __init__(self):
        self.name = None
        self.ons_code = None
        self.entity_type = OnsEntityTypes.NULL_ENTITY_TYPE
        self.geo_polygon = None
