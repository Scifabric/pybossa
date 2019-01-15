# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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

import inspect
from flask import abort
from flask_login import current_user
from pybossa.core import announcement_repo, task_repo, project_repo, result_repo
from pybossa.core import project_stats_repo
from pybossa.auth.errcodes import *

import jwt
from flask import jsonify
from jwt import exceptions

from . import project
from . import projectstats
from . import task
from . import taskrun
from . import category
from . import user
from . import token
from . import announcement
from . import blogpost
from . import auditlog
from . import webhook
from . import result
from . import helpingmaterial
from . import page

assert project
assert projectstats
assert task
assert taskrun
assert category
assert user
assert token
assert announcement
assert blogpost
assert auditlog
assert webhook
assert result
assert page


_actions = ['create', 'read', 'update', 'delete']
_auth_classes = {'project': project.ProjectAuth,
                 'projectstats': projectstats.ProjectStatsAuth,
                 'auditlog': auditlog.AuditlogAuth,
                 'announcement': announcement.AnnouncementAuth,
                 'blogpost': blogpost.BlogpostAuth,
                 'category': category.CategoryAuth,
                 'task': task.TaskAuth,
                 'taskrun': taskrun.TaskRunAuth,
                 'token': token.TokenAuth,
                 'user': user.UserAuth,
                 'webhook': webhook.WebhookAuth,
                 'result': result.ResultAuth,
                 'helpingmaterial': helpingmaterial.HelpingMaterialAuth,
                 'page': page.PageAuth
                 }


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
        if current_user.is_anonymous:
            raise abort(401)
        else:
            raise abort(403)
    return authorized


def _authorizer_for(resource_name):
    kwargs = {}
    if resource_name in ('project', 'taskrun'):
        kwargs.update({'task_repo': task_repo})
    if resource_name in ('auditlog', 'blogpost', 'task',
                         'taskrun', 'webhook', 'result',
                         'helpingmaterial', 'page'):
        kwargs.update({'project_repo': project_repo})
    if resource_name in ('project', 'task', 'taskrun'):
        kwargs.update({'result_repo': result_repo})
    return _auth_classes[resource_name](**kwargs)


def handle_error(error):
    """Return authentication error in JSON."""
    resp = jsonify(error)
    resp.status_code = 401
    return resp


def jwt_authorize_project(project, payload):
    """Authorize the project for the payload."""
    try:
        if payload is None:
            return handle_error(INVALID_HEADER_MISSING)
        parts = payload.split()

        if type(parts[0]) == bytes:
            b = parts[0].lower()
        else:
            b = str(parts[0].lower()).encode('utf-8')

        if b != b'bearer':
            return handle_error(INVALID_HEADER_BEARER)
        elif len(parts) == 1:
            return handle_error(INVALID_HEADER_TOKEN)
        elif len(parts) > 2:
            return handle_error(INVALID_HEADER_BEARER_TOKEN)

        data = jwt.decode(parts[1],
                          project.secret_key,
                          'H256')
        if (data['project_id'] == project.id
            and data['short_name'] == project.short_name):
            return True
        else:
            return handle_error(WRONG_PROJECT_SIGNATURE)
    except exceptions.DecodeError:
        return handle_error(DECODE_ERROR_SIGNATURE)
