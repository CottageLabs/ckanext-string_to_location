import cgi
import codecs
import pandas

from ckan.common import config
import ckan.lib.helpers as helpers
import ckan.lib.uploader as uploader
import ckan.logic as logic
import ckan.model
import ckan.plugins.toolkit as toolkit

from ckanext.string_to_location.location_mapper import LocationMapper
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter

# FIXME comments EVIL HACK
def perform(resource_id, username):
    '''
    Background job
    '''

    context = None
    resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

    log_writer = LocationMapperLogWriter(resource['id'])

    #
    # Validation
    # TODO: This is carried out in the controller, so we need to either:
    #   1. Trust that the input is good...
    #   2. Refactor this into a common place to keep it DRY
    #
    if 'location_column' in resource and 'location_type' in resource:
        column_name = resource['location_column']
        column_type=resource['location_type']
        is_name = resource['location_type'].endswith('_name')
    elif 'location_column' in resource['_extras'] and 'location_type' in resource['_extras']:
        extras = ast.literal_eval(resource['_extras'])
        column_name = extras['location_column']
        column_type=extras['location_type']
        is_name = extras['location_type'].endswith('_name')
    else:
        column_name = None
        column_type = None
        is_name = None

    if column_name is None:
        log_writer.error("The resource does not specify location columns", state="Something went wrong")


    resource_path = uploader.get_resource_uploader(resource).get_path(resource['id'])
    resource_contents = codecs.open(resource_path, 'rb', 'cp1257')

    table = pandas.read_csv(resource_contents)

    log_writer.info("Loaded contents of " + resource['name'])

    output_buffer = LocationMapper(table, column_name, column_type, is_name).map_location()

    upload = cgi.FieldStorage()
    # FIXME: replace with source filename + modified extension
    upload.filename = 'mapped_output.geojson'
    upload.file = output_buffer

    data_dict = {
        "package_id": resource['package_id'],
        "name": "Augmented " + resource['name'],
        "description": "Geo-mapped representation of " + resource['name'],
        "format": "application/geo+json",
        "upload": upload
    }

    new_resource = logic.action.create.resource_create(
        {"model": ckan.model, "ignore_auth": True, "user": username}, data_dict)

    # Update the user-facing log
    log_writer.info("Added new resource to dataset "
                    + config.get('ckan.site_url')
                    + helpers.url_for(controller='package',
                                      action='resource_read',
                                      id=new_resource['package_id'],
                                      resource_id=new_resource['id']),
                    state="complete")
