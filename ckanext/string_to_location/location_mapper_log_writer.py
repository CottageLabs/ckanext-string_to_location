import ckan.logic as logic
import ckan.plugins as p
from ckan.common import config
import json
import logging
import datetime


class LocationMapperLogWriter:

    def __init__(self, resource_id):
        self.resource_id = resource_id

    def info(self, message, state=None, context=None):
        self._log("INFO", message, state, context)

    def warn(self, message, state=None, context=None):
        self._log("WARN", message, state, context)

    def error(self, message, state=None, context=None):
        self._log("ERROR", message, state, context)

    def _log(self, log_level, message, state, context):
        """The types of log levels the interface knows about are:
            'INFO'
            'WARN'
            'ERROR'
        """

        now = str(datetime.datetime.utcnow())

        log = {'level': log_level, 'message': message, 'timestamp': now}

        try:
            existing_task = p.toolkit.get_action('task_status_show')(context, {
                'entity_id': self.resource_id,
                'task_type': 'location_mapper',
                'key': 'location_mapper'
            })
            task = existing_task
            
            if state:
                task['state'] = state

            if task['state'] is None:
                task['state'] = 'processing'
                
        except logic.NotFound:
            task = self._create_task(self.resource_id, state)

        value = json.loads(task['value'])

        value['logs'].append(log)
        task['value'] = json.dumps(value)
        task['last_updated'] = now

        p.toolkit.get_action('task_status_update')(context, task)

    @classmethod
    def _create_task(self, resource_id, state):
        return {
            'entity_id': resource_id,
            'entity_type': 'resource',
            'task_type': 'location_mapper',
            'last_updated': str(datetime.datetime.utcnow()),
            'state': state,
            'key': 'location_mapper',
            'value': json.dumps({"logs": []}),
            'error': '{}'
        }
