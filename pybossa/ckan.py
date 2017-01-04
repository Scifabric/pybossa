# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""CKAN module for PYBOSSA."""
import requests
import json
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun


class Ckan(object):

    """Class for CKAN service."""

    def _field_setup(self, obj):
        int_fields = ['id', 'project_id', 'task_id', 'user_id',
                      'n_answers', 'timeout', 'calibration', 'quorum']
        text_fields = ['state', 'user_ip']
        float_fields = ['priority_0']
        timestamp_fields = ['created', 'finish_time']
        json_fields = ['info']
        # Backrefs and functions
        sqlalchemy_refs = ['project', 'task_runs', 'pct_status']
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
                    fields.append({'id': "%s_%s" % (obj.__name__, attr),
                                   'type': 'int'})
        return fields

    def __init__(self, url, api_key=None):
        """Init method."""
        self.url = url + "/api/3"
        self.headers = {'Authorization': api_key,
                        'Content-type': 'application/json'}
        self.package = None
        self.aliases = dict(task="task", task_run="task_run, answer")
        self.fields = dict(task=self._field_setup(Task),
                           task_run=self._field_setup(TaskRun))
        self.primary_key = dict(task='id', task_run='id')
        self.indexes = dict(task='id', task_run='id')

    def get_resource_id(self, name):
        """Get resource ID from name."""
        for r in self.package['resources']:
            if r['name'] == name:
                return r['id']
        return False

    def package_exists(self, name):
        """Check if package exists."""
        pkg = {'id': name}
        r = requests.get(self.url + "/action/package_show",
                         headers=self.headers,
                         params=pkg)
        if r.status_code == 200 or r.status_code == 404 or r.status_code == 403:
            try:
                output = json.loads(r.text)
                if output.get('success'):
                    self.package = output['result']
                    return output['result'], None
                else:
                    return False, None
            except ValueError:
                return False, Exception("CKAN: JSON not valid", r.text,
                                        r.status_code)
        else:
            raise Exception("CKAN: the remote site failed! package_show failed",
                            r.text,
                            r.status_code)

    def package_create(self, project, user, url):
        """Create package."""
        pkg = {'name': project.short_name,
               'title': project.name,
               'author': user.fullname,
               'author_email': user.email_addr,
               'notes': project.description,
               'type': 'pybossa',
               'url': url}
        r = requests.post(self.url + "/action/package_create",
                          headers=self.headers,
                          data=json.dumps(pkg))
        if r.status_code == 200:
            output = json.loads(r.text)
            self.package = output['result']
            return self.package
        else:
            msg = "CKAN: the remote site failed! package_create failed"
            raise Exception(msg,
                            r.text,
                            r.status_code)

    def package_update(self, project, user, url, resources):
        """Update package."""
        pkg = {'id': project.short_name,
               'name': project.short_name,
               'title': project.name,
               'author': user.fullname,
               'author_email': user.email_addr,
               'notes': project.description,
               'type': 'pybossa',
               'resources': resources,
               'url': url}
        r = requests.post(self.url + "/action/package_update",
                          headers=self.headers,
                          data=json.dumps(pkg))
        if r.status_code == 200:
            output = json.loads(r.text)
            self.package = output['result']
            return self.package
        else:
            msg = "CKAN: the remote site failed! package_update failed"
            raise Exception(msg,
                            r.text,
                            r.status_code)

    def resource_create(self, name, package_id=None):
        """Create resource."""
        if package_id is None:
            package_id = self.package['id']
        rsrc = {'package_id': package_id,
                'name': name,
                'url': self.package['url'],
                'description': "%ss" % name}
        r = requests.post(self.url + "/action/resource_create",
                          headers=self.headers,
                          data=json.dumps(rsrc))
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            msg = "CKAN: the remote site failed! resource_create failed"
            raise Exception(msg,
                            r.text,
                            r.status_code)

    def datastore_create(self, name, resource_id=None):
        """Create datastore."""
        if resource_id is None:
            resource_id = self.get_resource_id(name)
        datastore = {'resource_id': resource_id,
                     'fields': self.fields[name],
                     'indexes': self.indexes[name],
                     'primary_key': self.primary_key[name],
                     'force': True}
        r = requests.post(self.url + "/action/datastore_create",
                          headers=self.headers,
                          data=json.dumps(datastore))

        if r.status_code == 200:
            output = json.loads(r.text)
            if output['success']:
                return output['result']
            else:  # pragma: no cover
                return output
        else:
            msg = "CKAN: the remote site failed! datastore_create failed"
            raise Exception(msg,
                            r.text,
                            r.status_code)

    def datastore_upsert(self, name, records, resource_id=None):
        """Upsert datastore."""
        if resource_id is None:
            resource_id = self.get_resource_id(name)
        _records = ''
        for text in records:
            _records += text
        _records = json.loads(_records)
        for i in range(0, len(_records), 20):
            chunk = _records[i:i + 20]
            payload = {'resource_id': resource_id,
                       'records': chunk,
                       'method': 'insert',
                       'force': True}
            r = requests.post(self.url + "/action/datastore_upsert",
                              headers=self.headers,
                              data=json.dumps(payload))
            if r.status_code != 200:
                msg = "CKAN: the remote site failed! datastore_upsert failed"
                raise Exception(msg,
                                r.text,
                                r.status_code)
        return True

    def datastore_delete(self, name, resource_id=None):
        """Delete datastore."""
        payload = {'resource_id': resource_id, 'force': True}
        r = requests.post(self.url + "/action/datastore_delete",
                          headers=self.headers,
                          data=json.dumps(payload))
        if r.status_code == 404 or r.status_code == 200:
            return True
        else:
            msg = "CKAN: the remote site failed! datastore_delete failed"
            raise Exception(msg,
                            r.text,
                            r.status_code)
