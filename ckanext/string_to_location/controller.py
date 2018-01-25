from ckan.lib.base import render
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
from ckan.controllers.package import PackageController

from ckanext.string_to_location.location_mapper import LocationMapper
from ckanext.string_to_location.location_mapper_log_reader import LocationMapperLogReader

class LocationMapperController(PackageController):

    def map_location(self, id, resource_id):
        context = None

        resource = toolkit.get_action('resource_show')(
            context, {'id': resource_id})

        LocationMapper(resource).map_location()

        return helpers.redirect_to(controller='ckanext.string_to_location.controller:LocationMapperController',
                                   action='resource_location_mapping_status', id=id, resource_id=resource_id)

    def resource_location_mapping_status(self, id, resource_id):

        context = None

        try:
            toolkit.c.pkg_dict = toolkit.get_action('package_show')(
                context, {'id': id}
            )
            toolkit.c.resource = toolkit.get_action('resource_show')(
                context, {'id': resource_id}
            )
        except (logic.NotFound, logic.NotAuthorized):
            base.abort(404, _('Resource not found'))

        log_reader = LocationMapperLogReader(resource_id)

        status = log_reader.get_status()

        return render('custom/resource_location_mapping_status.html',
                           extra_vars={'status': status})
