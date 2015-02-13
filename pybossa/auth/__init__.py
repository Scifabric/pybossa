# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

import inspect
from flask import abort
from flask.ext.login import current_user
from pybossa.core import task_repo, project_repo

import app
import task
import taskrun
import category
import user
import token
import blogpost
import auditlog

assert app
assert task
assert taskrun
assert category
assert user
assert token
assert blogpost
assert auditlog


class Authorizer(object):
    actions = ['create', 'read', 'update', 'delete']
    auth_classes = {'app': app.AppAuth,
                    'auditlog': auditlog.AuditlogAuth,
                    'taskrun': taskrun.TaskRunAuth}


    def is_authorized(self, user, action, resource):
        assert action in self.actions
        is_class = inspect.isclass(resource)
        name = resource.__name__ if is_class else resource.__class__.__name__
        resource = None if is_class else resource
        auth = self._authorizer_for(name.lower())
        return auth.can(user, action, resource)

    def ensure_authorized(self, action, resource):
        authorized = self.is_authorized(current_user, action, resource)
        if authorized is False:
            if current_user.is_anonymous():
                raise abort(401)
            else:
                raise abort(403)
        return authorized


    def _authorizer_for(self, resource_name):
        kwargs = {}
        print resource_name
        if resource_name == 'taskrun':
            kwargs = {'task_repo': task_repo, 'project_repo': project_repo}
        if resource_name == 'auditlog':
            kwargs = {'project_repo': project_repo}
        return self.auth_classes[resource_name](**kwargs)



require = Authorizer()











