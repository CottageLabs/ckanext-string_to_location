# encoding: utf-8

'''Tests for the ckanext.string_to_location.plugin module.'''

from nose.tools import assert_true, assert_in
from StringIO import StringIO

import paste.fixture
import pylons.test
import json
import csv
import cgi

import ckan.model as model
import ckan.plugins
import ckan.lib.helpers as h
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers


from ckan.lib.helpers import url_for
from ckan.common import config

from ckanext.string_to_location.location_mapper_log_reader import LocationMapperLogReader
from ckanext.string_to_location.location_mapper_log_writer import LocationMapperLogWriter


class TestString_To_LocationPlugin(object):

    @classmethod
    def setup_class(cls):
        cls.original_config = config.copy()
        if not ckan.plugins.plugin_loaded('string_to_location'):
            ckan.plugins.load('string_to_location')

    def teardown(self):
        model.repo.rebuild_db()
        ckan.lib.search.clear_all()

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()
        config.update(cls.original_config)
        ckan.plugins.unload('string_to_location')

    def test_write_info_log_message_for_a_resource(self):
        user, resource, context = self._create_context()

        log_writer = LocationMapperLogWriter(resource['id'])
        log_writer.info("Testing", context=context)

        task = ckan.plugins.toolkit.get_action('task_status_show')(context, {
            'entity_id': resource['id'],
            'task_type': 'location_mapper',
            'key': 'location_mapper'
        })

        value = json.loads(task['value'])

        assert_true(value['logs'][0]['message'], "Testing")

    def test_write_warn_log_message_for_a_resource(self):
        user, resource, context = self._create_context()

        log_writer = LocationMapperLogWriter(resource['id'])
        log_writer.warn("Warning", context=context)

        task = ckan.plugins.toolkit.get_action('task_status_show')(context, {
            'entity_id': resource['id'],
            'task_type': 'location_mapper',
            'key': 'location_mapper'
        })

        value = json.loads(task['value'])

        assert_true(value['logs'][0]['message'], "Warning")

    def test_write_error_log_message_for_a_resource(self):
        user, resource, context = self._create_context()

        log_writer = LocationMapperLogWriter(resource['id'])
        log_writer.error("Oops", context=context)

        task = ckan.plugins.toolkit.get_action('task_status_show')(context, {
            'entity_id': resource['id'],
            'task_type': 'location_mapper',
            'key': 'location_mapper'
        })

        value = json.loads(task['value'])

        assert_true(value['logs'][0]['message'], "Oops")

    def test_read_log_message_for_a_resource(self):
        user, resource, context = self._create_context()

        log_writer = LocationMapperLogWriter(resource['id'])
        log_writer.info("Testing", context=context)

        log_reader = LocationMapperLogReader(resource['id'])
        mapper_status = log_reader.get_status()

        assert_true(mapper_status['task_info'][
                    'logs'][0]['message'], "Testing")

    def test_map_location_with_correctly_formatted_file(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._create_correctly_formatted_csv()

        extras = {
            "location_column" : "Local authority",
            "location_type" : "local_authority_name" 
        }

        resource, package = self._create_csv_resource(output_buffer, extras)
       

        response = helpers.webtest_maybe_follow(app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location",
            extra_environ={'REMOTE_USER': str(user['name'])}))

        response.mustcontain('Complete')

    def test_location_mapper_tab_contains_new_resource_url(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._create_correctly_formatted_csv()

        extras = {
            "location_column" : "Local authority",
            "location_type" : "local_authority_name" 
        }

        resource, package = self._create_csv_resource(output_buffer, extras)
       

        response = helpers.webtest_maybe_follow(app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location",
            extra_environ={'REMOTE_USER': str(user['name'])}))

        response.mustcontain("Added new resource to dataset " \
                                + config.get('ckan.site_url')  \
                                + h.url_for(controller='package', 
                                                action='resource_read', 
                                                id=resource['package_id'], 
                                                resource_id=resource['id']))

    def test_map_location_with_correctly_formatted_file_uploads_expected_resources_to_dataset(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._create_correctly_formatted_csv()

        extras = {
            "location_column" : "Local authority",
            "location_type" : "local_authority_name" 
        }

        resource, package = self._create_csv_resource(output_buffer, extras)
       

        helpers.webtest_maybe_follow(app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location",
            extra_environ={'REMOTE_USER': str(user['name'])}))

        package = helpers.call_action('package_show', id=resource['package_id'])
        
        assert_true((len(package['resources'])), 2)

    def test_map_location_with_missing_resource_information(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._create_correctly_formatted_csv()

        resource, package = self._create_csv_resource(output_buffer)

        response = helpers.webtest_maybe_follow(app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location",
            extra_environ={'REMOTE_USER': str(user['name'])})) 

        response.mustcontain("The resource does not specify location columns")   
    
    def test_map_location_with_incorrectly_formatted_file(self):
        # FIXME add test when we have handling for incorrectly formatted files
        pass
        
    def test_map_location_with_incorrectly_formatted_file_no_uploads_to_dataset(self):
        # FIXME add test when we have handling for incorrectly formatted files
        pass

    def _create_context(self):
        user = factories.Sysadmin()
        resource = factories.Resource()

        context = {
            'user': user['name']
        }

        return user, resource, context

    def _create_correctly_formatted_csv(self):
        output_buffer = StringIO()

        data = [["Local authority", "Number"], ["Birmingham", 10]]
        writer = csv.writer(output_buffer)
        writer.writerows(data)

        return output_buffer

    def _create_csv_resource(self, file, extras={}):
        package = factories.Dataset()

        upload = cgi.FieldStorage()
        upload.filename = 'test.csv'
        upload.file = file

        resource = helpers.call_action('resource_create', 
            package_id=package['id'], 
            name="test.csv", 
            format="text/csv",
            _extras=extras, 
            upload=upload)

        return resource, package