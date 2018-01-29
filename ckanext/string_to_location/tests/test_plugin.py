# encoding: utf-8

'''Tests for the ckanext.string_to_location.plugin module.'''

from nose.tools import assert_true, assert_in
from StringIO import StringIO

import paste.fixture
import pylons.test
import json
import csv
import cgi
import operator

import ckan.model as model
import ckan.plugins
import ckan.lib.helpers as h
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers


from ckan.lib.helpers import url_for
from ckan.common import config


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

    def test_map_location_with_local_authority_district(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._create_correctly_formatted_csv()

        extras = {
            "location_column" : "Local Authority District",
            "location_type" : "local_authority_district_name" 
        }

        resource, package = self._create_csv_resource(output_buffer, extras)
       

        response = helpers.webtest_maybe_follow(app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location",
            extra_environ={'REMOTE_USER': str(user['name'])}))

        response.mustcontain('Complete')

    def test_map_location_with_local_authority_district_named_puppies(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._create_correctly_formatted_puppies_csv()

        extras = {
            "location_column" : "Puppies",
            "location_type" : "local_authority_district_name" 
        }

        resource, package = self._create_csv_resource(output_buffer, extras)
       

        response = helpers.webtest_maybe_follow(app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location",
            extra_environ={'REMOTE_USER': str(user['name'])}))

        response.mustcontain('Complete')

    def test_map_location_with_sample_file(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._load_correctly_formatted_csv()

        extras = {
            "location_column" : "Local authority",
            "location_type" : "local_authority_district_name" 
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
            "location_column" : "Local Authority District",
            "location_type" : "local_authority_district_name" 
        }

        resource, package = self._create_csv_resource(output_buffer, extras)
       

        response = helpers.webtest_maybe_follow(app.get("/dataset/" + package['id'] + "/resource/" + resource['id']+ "/map_location",
            extra_environ={'REMOTE_USER': str(user['name'])}))

        # refresh the package
        package = helpers.call_action('package_show', id=package['id'])

        # get the resource list for the package, sort them in descending order so the most recently created on is first

        resources = sorted(package['resources'], key=operator.itemgetter('created'), reverse=True)

        new_resource = resources[0]

        response.mustcontain("Added new resource to dataset " \
                                + config.get('ckan.site_url')  \
                                + h.url_for(controller='package', 
                                            action='resource_read', 
                                            id=new_resource['package_id'], 
                                            resource_id=new_resource['id']))

    def test_map_location_with_correctly_formatted_file_uploads_expected_resources_to_dataset(self):
        app = helpers.FunctionalTestBase._get_test_app()
        user, resource, context = self._create_context()

        output_buffer = self._create_correctly_formatted_csv()

        extras = {
            "location_column" : "Local Authority District",
            "location_type" : "local_authority_district_name" 
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

    def _create_context(self):
        user = factories.Sysadmin()
        resource = factories.Resource()

        context = {
            'user': user['name']
        }

        return user, resource, context

    def _create_correctly_formatted_csv(self):
        output_buffer = StringIO()

        data = [["Local Authority District", "Number"], ["Birmingham", 10]]
        writer = csv.writer(output_buffer)
        writer.writerows(data)

        return output_buffer

    def _create_correctly_formatted_puppies_csv(self):
        output_buffer = StringIO()

        data = [["Puppies", "Number"], ["Birmingham", 10]]
        writer = csv.writer(output_buffer)
        writer.writerows(data)

        return output_buffer

    def _load_correctly_formatted_csv(self):
        output_buffer = StringIO()

        data = csv.reader(open("ckanext/string_to_location/tests/test_data/test_local_authority.csv"))
        
        writer = csv.writer(output_buffer)
        writer.writerows(data)

        return output_buffer


    def _create_csv_resource(self, file, extras={}):
        package = factories.Dataset()
        print("This is the package")
        print(package)

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