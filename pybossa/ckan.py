import requests
import json

from pybossa.model import Task, TaskRun


class Ckan(object):
    def _field_setup(self, obj):
        int_fields = ['id', 'app_id', 'task_id', 'user_id', 'n_answers', 'timeout',
                      'calibration', 'quorum']
        text_fields = ['state', 'user_ip']
        float_fields = ['priority_0']
        timestamp_fields = ['created', 'finish_time']
        json_fields = ['info']
        # Backrefs and functions
        sqlalchemy_refs = ['app', 'task_runs', 'pct_status']
        fields = []
        for attr in obj.__dict__.keys():
            if ("__" not in attr[0:2] and "_" not in attr[0:1] and
                    attr not in sqlalchemy_refs):
                if attr in json_fields:
                    fields.append({'id': attr, 'type': 'json'})
                elif attr in timestamp_fields:
                    fields.append({'id': attr, 'type': 'timestamp'})
                elif attr in int_fields:
                    fields.append({'id': attr, 'type': 'int'})
                elif attr in text_fields:
                    fields.append({'id': attr, 'type': 'text'})
                elif attr in float_fields:
                    fields.append({'id': attr, 'type': 'float'})
                else:
                    fields.append({'id': attr})
        return fields

    def __init__(self, url, api_key):
        self.url = url
        self.headers = {'Authorization': api_key,
                        'Content-type': 'application/json'}
        self.package = None
        self.aliases = dict(task="task", task_run="task_run, answer")
        self.fields = dict(task=self._field_setup(Task), task_run=self._field_setup(TaskRun))
        self.primary_key = dict(task='id', task_run='id')
        self.indexes = dict(task='id', task_run='id')

    def package_exists(self, name):
        pkg = {'id': name}
        r = requests.get(self.url + "/action/package_show",
                         headers=self.headers,
                         params=pkg)
        output = r.json()
        if output.get('success'):
            self.package = output['result']
            return output['result']
        else:
            return False

    def package_create(self, app, user, url):
        pkg = {'name': app.short_name,
               'title': app.name,
               'author': user.fullname,
               'url': url}
        r = requests.post(self.url + "/action/package_create",
                          headers=self.headers,
                          data=json.dumps(pkg))
        self.package = r.json()
        return self.package

    def resource_create(self, name):
        rsrc = {'package_id': self.package['id'],
                'name': name,
                'url': self.package['url'],
                'description': "%ss" % name}
        r = requests.post(self.url + "/action/resource_create",
                          headers=self.headers,
                          data=json.dumps(rsrc))
        return r.json()

    def datastore_create(self, name):
        rsrc = None
        for r in self.package['resources']:
            if r['name'] == name:
                rsrc = r
                break
        datastore = {'resource_id': rsrc['id'],
                     'aliases': self.aliases[name],
                     'fields': self.fields[name],
                     'indexes': self.indexes[name]}
        r = requests.post(self.url + "/action/datastore_create",
                          headers=self.headers,
                          data=json.dumps(datastore))
        return r.json()
