import cgi
import codecs
import geojson
import logging
import pandas
from StringIO import StringIO

from ckan.common import config
import ckan.lib.helpers as helpers
import ckan.lib.uploader as uploader
import ckan.logic as logic
import ckan.model
import ckan.plugins.toolkit as toolkit

from ckanext.string_to_location.exceptions import LookupNameMissingException
from ckanext.string_to_location.location_mapper import LocationMapper
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter

# FIXME comments EVIL HACK
def perform(resource_id, column_name, column_type, is_name, username):
    '''
    Background job
    '''
    context = None
    resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

    log_writer = LocationMapperLogWriter(resource['id'])

    try:
        table = __read_csv_from_resource(resource)

        row_count = table.shape[0]
        column_count = table.shape[1]
        log_writer.info("Loaded resource contents: " + str(row_count) + " rows, " + str(column_count) + " columns")

        # This throws a LookupNameMissingException if the column doesn't exist in the resource
        geojson_version = LocationMapper(table, column_name, column_type, is_name).map_and_build_geojson()

        match_percentage = len(geojson_version.features) / float(row_count)
        log_writer.info("Matched ONS GeoJSON objects: {} of {} ({:.1%})".format(len(geojson_version.features), row_count, match_percentage))

        new_resource = __create_and_upload_geojson_resource(package_id=resource['package_id'],
                                                    name="Augmented " + resource['name'],
                                                    description="Geo-mapped representation of " + resource['name'],
                                                    filename='mapped_output.geojson',
                                                    geojson_obj=geojson_version,
                                                    username=username)

        # Update the user-facing log
        log_writer.info("Added new resource to dataset {}{}".format(
                            config.get('ckan.site_url'),
                            helpers.url_for(controller='package',
                                            action='resource_read',
                                            id=new_resource['package_id'],
                                            resource_id=new_resource['id'])))

        log_writer.info("Location mapping completed", state="complete")

    except LookupNameMissingException:
        '''
        LocationMapper raises this exception if the location column isn't found, so we mirror
        that into the user-facing task log.
        '''
        log_writer.error("The location column '{}' wasn't found in the resource file".format(column_name), state="Something went wrong")

    except Exception as exception:
        '''
        Catch ALL THE THINGS!

        In the event of something unexpected, for example a syntax error, malformed input, etc.,
        we need to feed back to the user in the Location Mapper task log so they can see the task
        has failed.

        Even though a misc error (oh, the specificity!) has been caught, we record this in the UI,
        but treat the RQ job as being successful. This is to prevent them being queued up again.
        '''
        log_writer.error("An error occurred in the code! Please check the system logs.", state="Something went wrong")
        logging.exception(exception)
        pass

def __read_csv_from_resource(resource):
    resource_path = uploader.get_resource_uploader(resource).get_path(resource['id'])
    resource_contents = codecs.open(resource_path, 'rb', 'cp1257')

    return pandas.read_csv(resource_contents)

def __create_and_upload_geojson_resource(package_id, name, description, filename, geojson_obj, username):
    file_buffer = StringIO()
    geojson.dump(geojson_obj, file_buffer, ignore_nan=True)

    upload = cgi.FieldStorage()
    upload.filename = filename
    upload.file = file_buffer

    data_dict = {
        "package_id": package_id,
        "name": name,
        "description": description,
        "format": "application/geo+json",
        "upload": upload
    }

    return logic.action.create.resource_create({"model": ckan.model,
                                                "ignore_auth": True,
                                                "user": username}, data_dict)
