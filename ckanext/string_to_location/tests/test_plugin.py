# encoding: utf-8

'''Tests for the ckanext.string_to_location.plugin module.'''

from nose.tools import assert_true, assert_in

import paste.fixture
import pylons.test
import json

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

    def _create_context(self):
        user = factories.Sysadmin()
        resource = factories.Resource()

        context = {
            'user': user['name']
        }

        return user, resource, context