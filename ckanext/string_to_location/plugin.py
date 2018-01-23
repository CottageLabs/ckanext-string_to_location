import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class String_To_LocationPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IRoutes

    def before_map(self, map):
        map.connect('/dataset/{id}/resource/{resource_id}/map_location',
                    controller='ckanext.string_to_location.controller:LocationMapperController',
                    action='map_location')
        map.connect(
            'resource_location_mapping_status', '/dataset/{id}/resource_location_mapping_status/{resource_id}',
            controller='ckanext.string_to_location.controller:LocationMapperController',
            action='resource_location_mapping_status')
        return map

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'string_to_location')