class OnsEntity:
    """An ONS object, e.g. Local Authority District

    """

    def __init__(self, name, ons_code, entity_type, geo_polygon):
        """
        `entity_type` should be an OnsEntityTypes constant
        """
        self.name = name
        self.ons_code = ons_code
        self.entity_type = entity_type
        self.geo_polygon = geo_polygon
