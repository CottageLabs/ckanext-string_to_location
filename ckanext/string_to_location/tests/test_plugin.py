# encoding: utf-8

'''Tests for the ckanext.string_to_location.plugin module.'''

from nose.tools import assert_true, assert_in

import paste.fixture
import pylons.test
import json
import csv

import ckan.model as model
import ckan.plugins
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
        file = self._create_correctly_formatted_csv()
        resource, package = self._create_csv_resource(file)

        response = app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location")

        response.mustcontain('Complete')

    # def test_map_location_with_incorrectly_formatted_file(self):
    #     file = self._create_incorrectly_formatted_csv()        
    #     resource, package = self._create_csv_resource(file)

    #     response = 
    #     # hit the map location route with that resource id
    #     # expect the response to be a server error
    #     pass

    # def test_map_location_with_correctly_formatted_file_uploads_expected_resources_to_dataset(self):
    #     file = self._create_correctly_formatted_csv()        
    #     resource, package = self._create_csv_resource(file)
    #     # hit the map location url with corret data
    #     # check that the dataset has the expected additional resources attached
    #     pass

    # def test_map_location_with_incorrectly_formatted_file_no_uploads_to_dataset(self):
    #     file = self._create_incorrectly_formatted_csv()        
    #     resource, package = self._create_csv_resource(file)
    #     # hit the map location url with wrong data
    #     # check that the dataset has no additional resources attached
    #     pass

    def _create_context(self):
        user = factories.Sysadmin()
        resource = factories.Resource()

        context = {
            'user': user['name']
        }

        return user, resource, context

    def _create_correctly_formatted_csv(self):
        data = [["Local authority", "Number"], ["Birmingham", 10]]
        with open('test.csv', 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(data)

    def _create_incorrectly_formatted_csv(self):
        data = [["Puppies", "Number"], ["Birmingham", 10]]
        with open('test.csv', 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(data)

    def _create_csv_resource(self, file):
        package = factories.Dataset()
        resource = helpers.call_action('resource_create', 
            name="test.csv", 
            upload=file, 
            package_id=package['id']
            )

        return resource, package