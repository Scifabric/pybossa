import requests
import json

from pybossa.model import Task, TaskRun


class Ckan(object):
    aliases = dict(task="task", task_run="task_run, answer")
    fields = dict(task=[{'id': attr} for attr in Task.__dict__.keys()
                        if "__" not in attr[0:2] and "_" not in attr[0:1]],
                  task_run=[{'id': attr} for attr in TaskRun.__dict__.keys()
                            if "__" not in attr and "_" not in attr[0:1]])
    indexes = dict(task='id', task_run='id')

    def __init__(self, url, api_key):
        self.url = url
        self.headers = {'Authorization': api_key,
                        'Content-type': 'application/json'}
        self.package = None
        self.resource = dict(task=None, task_run=None)

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
                'url': self.package['url'],
                'description': name}
        r = requests.post(self.url + "/action/resource_create",
                          headers=self.headers,
                          data=json.dumps(rsrc))
        self.resource[name] = r.json()
        return self.resource[name]

    def datastore_create(self, name):
        if name == 'task':
            aliases = 'task'
        elif name == 'task_run':
            aliases = 'task_run, answers'
        else:
            return False
        datastore = {'resource_id': self.resource[name]['id'],
                     'aliases': aliases,
                     'fields': self.fields[name],
                     'indexes': self.indexes[name]}
