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
                    fields.append({'id': "%s_%s" % (obj.__name__, attr), 'type': 'int'})
        return fields

    def __init__(self, url, api_key):
        self.url = url + "/api/3/"
        self.headers = {'Authorization': api_key,
                        'Content-type': 'application/json'}
        self.package = None
        self.aliases = dict(task="task", task_run="task_run, answer")
        self.fields = dict(task=self._field_setup(Task), task_run=self._field_setup(TaskRun))
        self.primary_key = dict(task='id', task_run='id')
        self.indexes = dict(task='id', task_run='id')

    def get_resource_id(self, name):
        for r in self.package['resources']:
            if r['name'] == name:
                return r['id']
        return False

    def package_exists(self, name):
        pkg = {'id': name}
        r = requests.get(self.url + "/action/package_show",
                         headers=self.headers,
                         params=pkg)
        try:
            if r.status_code == 200 or r.status_code == 404:
                output = json.loads(r.text)
                if output.get('success'):
                    self.package = output['result']
                    return output['result']
                else:
                    return False
            else:
                raise Exception("CKAN: package_show failed",
                                r.text,
                                r.status_code)
        except Exception as inst:
            return inst

    def package_create(self, app, user, url):
        pkg = {'name': app.short_name,
               'title': app.name,
               'author': user.fullname,
               'url': url}
        r = requests.post(self.url + "/action/package_create",
                          headers=self.headers,
                          data=json.dumps(pkg))
        try:
            if r.status_code == 200:
                output = json.loads(r.text)
                self.package = output['result']
                return self.package
            else:
                raise Exception("CKAN: package_create failed",
                                r.text,
                                r.status_code)
        except Exception as inst:
            return inst

    def resource_create(self, name):
        rsrc = {'package_id': self.package['id'],
                'name': name,
                'url': self.package['url'],
                'description': "%ss" % name}
        r = requests.post(self.url + "/action/resource_create",
                          headers=self.headers,
                          data=json.dumps(rsrc))
        try:
            if r.status_code == 200:
                return json.loads(r.text)
            else:
                raise Exception("CKAN: resource_create failed",
                                r.text,
                                r.status_code)
        except Exception as inst:
            return inst

    def datastore_create(self, name, resource_id=None):
        if resource_id is None:
            resource_id = self.get_resource_id(name)
        datastore = {'resource_id': resource_id,
                     'fields': self.fields[name],
                     'indexes': self.indexes[name],
                     'primary_key': self.primary_key[name]}
        r = requests.post(self.url + "/action/datastore_create",
                          headers=self.headers,
                          data=json.dumps(datastore))
        try:
            if r.status_code == 200:
                output = json.loads(r.text)
                if output['success']:
                    return output['result']
                else:
                    return output
            else:
                raise Exception("CKAN: datastore_create failed",
                                r.text,
                                r.status_code)
        except Exception as inst:
            return inst

    def datastore_upsert(self, name, records, resource_id=None):
        if resource_id is None:
            resource_id = self.get_resource_id(name)
        _records = ''
        for text in records:
            _records += text
        _records = json.loads(_records)
        try:
            for i in range(0, len(_records), 20):
                chunk = _records[i:i + 20]
                payload = {'resource_id': resource_id,
                           'records': chunk,
                           'method': 'insert'}
                r = requests.post(self.url + "/action/datastore_upsert",
                                  headers=self.headers,
                                  data=json.dumps(payload))
                if r.status_code != 200:
                    raise Exception("CKAN: datastore_upsert failed",
                                    r.text,
                                    r.status_code)
            return True
        except Exception as inst:
            return inst

    def datastore_delete(self, name, resource_id=None):
        if resource_id is None:
            resource_id = self.get_resource_id(name)
        payload = {'resource_id': resource_id}
        r = requests.post(self.url + "/action/datastore_delete",
                          headers=self.headers,
                          data=json.dumps(payload))
        try:
            if r.status_code != 200:
                raise Exception("CKAN: datastore_delete failed",
                                r.text,
                                r.status_code)
            else:
                return True
        except Exception as inst:
            return inst
