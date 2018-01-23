import ckan.plugins as p
import ckan.logic as logic
import json
import logging


class LocationMapperLogReader:

    def __init__(self, resource_id):
        self.resource_id = resource_id

    def get_status(self):

        mapper_status = {}
        context = None

        try:
            task = p.toolkit.get_action('task_status_show')(context, {
                'entity_id': self.resource_id,
                'task_type': 'location_mapper',
                'key': 'location_mapper'
            })

            mapper_status = self._build_mapper_status(task)

            logging.warn(mapper_status)

        except logic.NotFound:
            mapper_status['task_info'] = {
                "error": "Looks like we haven't started mapping location for this resource."}

        return mapper_status

    @classmethod
    def _build_mapper_status(self, task):
        mapper_status = {
            'status': task['state'],
            'last_updated': task['last_updated'],
            'task_info': json.loads(task['value']),
            'error': json.loads(task['error'])
        }
        return mapper_status
