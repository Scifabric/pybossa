# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
from pybossa.core import task_repo, project_repo, result_repo

import project
import task
import taskrun
import category
import user
import token
import blogpost
import auditlog
import webhook
import result

assert project
assert task
assert taskrun
assert category
assert user
assert token
assert blogpost
assert auditlog
assert webhook
assert result


_actions = ['create', 'read', 'update', 'delete']
_auth_classes = {'project': project.ProjectAuth,
                 'auditlog': auditlog.AuditlogAuth,
                 'blogpost': blogpost.BlogpostAuth,
                 'category': category.CategoryAuth,
                 'task': task.TaskAuth,
                 'taskrun': taskrun.TaskRunAuth,
                 'token': token.TokenAuth,
                 'user': user.UserAuth,
                 'webhook': webhook.WebhookAuth,
                 'result': result.ResultAuth}


def is_authorized(user, action, resource, **kwargs):
    is_class = inspect.isclass(resource)
    name = resource.__name__ if is_class else resource.__class__.__name__
    if resource == 'token':
        name = resource
    resource = None if is_class else resource
    auth = _authorizer_for(name.lower())
    actions = _actions + auth.specific_actions
    assert action in actions, "%s is not a valid action" % action
    return auth.can(user, action, resource, **kwargs)


def ensure_authorized_to(action, resource, **kwargs):
    authorized = is_authorized(current_user, action, resource, **kwargs)
    if authorized is False:
        if current_user.is_anonymous():
            raise abort(401)
        else:
            raise abort(403)
    return authorized


def _authorizer_for(resource_name):
    kwargs = {}
    if resource_name in ('project', 'taskrun'):
        kwargs.update({'task_repo': task_repo})
    if resource_name in ('auditlog', 'blogpost', 'task',
                         'taskrun', 'webhook', 'result'):
        kwargs.update({'project_repo': project_repo})
    if resource_name in ('project', 'task', 'taskrun'):
        kwargs.update({'result_repo': result_repo})
    return _auth_classes[resource_name](**kwargs)
