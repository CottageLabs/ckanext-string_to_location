import ast

from ckan.controllers.package import PackageController
from ckan.lib.base import render
import ckan.common
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit

from ckanext.string_to_location.location_mapper import map_location_async
from ckanext.string_to_location.location_mapper_log_reader import LocationMapperLogReader
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter

class LocationMapperController(PackageController):

    def map_location(self, id, resource_id):
        context = None
        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

        # Validate the resource before pushing the job
        log_writer = LocationMapperLogWriter(resource['id'])

        if 'location_column' in resource and 'location_type' in resource:
            column_name = resource['location_column']
            column_type = resource['location_type']
            is_name = resource['location_type'].endswith('_name')
        elif 'location_column' in resource['_extras'] and 'location_type' in resource['_extras']:
            extras = ast.literal_eval(resource['_extras'])
            column_name = extras['location_column']
            column_type = extras['location_type']
            is_name = extras['location_type'].endswith('_name')
        else:
            column_name = None
            column_type = None
            is_name = None

        if column_name is None:
            log_writer.error("The resource does not specify location columns", state="Something went wrong")
        else:
            # Enqueue the location_mapping task
            ckan.plugins.toolkit.enqueue_job(map_location_async, [], {u'resource_id': resource['id'], u'username': ckan.common.c.userobj.name}, title='map_location_async')
            log_writer.info("Queued location mapping job TODO_ID")

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
