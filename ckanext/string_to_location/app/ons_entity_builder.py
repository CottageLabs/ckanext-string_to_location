from ons_code_lookup import OnsCodeLookup

from ons_entity import OnsEntity
from null_ons_entity import NullOnsEntity
from ons_polygon_lookup import OnsPolygonLookup


class OnsEntityBuilder:
    """
    TODO docs
    """

    @classmethod
    def build(cls, name_or_code, entity_type, is_name=True):
        """
        FIXME: this is a dirty hack! Think about a more elegant way of switching this
        """
        if is_name:
            return cls.from_name(name_or_code, entity_type)
        else:
            return cls.from_code(name_or_code, entity_type)

    @classmethod
    def from_name(cls, name, entity_type):
        """
        TODO docs
        """
        ons_code = OnsCodeLookup().code_for(entity_type, name)

        return cls.__build(name, ons_code, entity_type)

    @classmethod
    def from_code(cls, ons_code, entity_type):
        """
        TODO docs
        """
        name = OnsCodeLookup().name_for(ons_code)
        return cls.__build(name, ons_code, entity_type)

    @classmethod
    def __build(cls, name, ons_code, entity_type):
        if name is None or ons_code is None:
            return NullOnsEntity()

        geo_polygon = OnsPolygonLookup(entity_type, ons_code).call()

        return OnsEntity(
            name=name,
            entity_type=entity_type,
            ons_code=ons_code,
            geo_polygon=geo_polygon
        )
