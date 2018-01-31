import ast

from ckan.controllers.package import PackageController
from ckan.lib.base import render
import ckan.common
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit

from ckanext.string_to_location.location_mapper_job import perform as location_mapper_job
from ckanext.string_to_location.location_mapper_log_reader import LocationMapperLogReader
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter

class LocationMapperController(PackageController):

    def map_location(self, id, resource_id):
        context = None
        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

        # Validate the resource before pushing the job
        log_writer = LocationMapperLogWriter(resource['id'])

        column_name = resource.get('location_column', None) or ast.literal_eval(resource.get('_extras', '{}')).get('location_column', None)
        column_type = resource.get('location_type', None) or ast.literal_eval(resource.get('_extras', '{}')).get('location_type', None)
        is_name = column_type is not None and column_type.endswith('_name')

        if column_name and column_type:
            # Enqueue the location_mapping task
            job = ckan.plugins.toolkit.enqueue_job(location_mapper_job, [], {u'resource_id': resource['id'], u'column_name': column_name, u'column_type': column_type, u'is_name': is_name, u'username': ckan.common.c.userobj.name}, title='map_location_async')
            log_writer.info("Queued location mapping (Job ID:" + job.id + ")")
        else:
            if column_name is None:
                log_writer.error("Location column not specified for resource", state="Something went wrong")

            if column_type is None:
                log_writer.error("Location type not specified for resource", state="Something went wrong")

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
