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
"""
PyBossa api module for exposing domain objects via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * projects,
    * categories,
    * tasks,
    * task_runs,
    * users,
    * global_stats,
    * vmcp

"""

import json
from flask import Blueprint, request, abort, Response, \
    current_app, make_response
from flask.ext.login import current_user
from werkzeug.exceptions import NotFound
from pybossa.util import jsonpify, crossdomain
import pybossa.model as model
from pybossa.core import db, csrf, ratelimits
from itsdangerous import URLSafeSerializer
from pybossa.ratelimit import ratelimit
import pybossa.sched as sched
from pybossa.error import ErrorStatus
from global_stats import GlobalStatsAPI
from task import TaskAPI
from task_run import TaskRunAPI
from app import AppAPI
from category import CategoryAPI
from vmcp import VmcpAPI
from user import UserAPI
from token import TokenAPI

blueprint = Blueprint('api', __name__)

cors_headers = ['Content-Type', 'Authorization']

error = ErrorStatus()

api_versions = ['v0', 'v1.0']


@blueprint.route('/', defaults={'version': 'v0'})
@blueprint.route('/<version>/')
@crossdomain(origin='*', headers=cors_headers)
@ratelimit(limit=ratelimits['LIMIT'], per=ratelimits['PER'])
def index(version):  # pragma: no cover
    """Return dummy text for welcome page."""
    if version in api_versions:
        return 'The PyBossa API %s' % version
    else:
        return abort(404)


def register_api(view, endpoint, url, pk='id', pk_type='int'):
    """Register API endpoints.

    Registers new end points for the API using classes.

    """
    view_func = view.as_view(endpoint)
    csrf.exempt(view_func)
    blueprint.add_url_rule(url,
                           view_func=view_func,
                           defaults={pk: None, 'version': 'v0'},
                           methods=['GET', 'OPTIONS'])
    blueprint.add_url_rule(url,
                           view_func=view_func,
                           defaults={'version': 'v0'},
                           methods=['POST', 'OPTIONS'])
    blueprint.add_url_rule('%s/<%s:%s>' % (url, pk_type, pk),
                           view_func=view_func,
                           defaults={'version': 'v0'},
                           methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])

    blueprint.add_url_rule('/<version>%s/<%s:%s>' % (url, pk_type, pk),
                           view_func=view_func,
                           methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])


register_api(AppAPI, 'api_app', '/app', pk='id', pk_type='int')
register_api(CategoryAPI, 'api_category', '/category', pk='id', pk_type='int')
register_api(TaskAPI, 'api_task', '/task', pk='id', pk_type='int')
register_api(TaskRunAPI, 'api_taskrun', '/taskrun', pk='id', pk_type='int')
register_api(UserAPI, 'api_user', '/user', pk='id', pk_type='int')
register_api(GlobalStatsAPI, 'api_globalstats', '/globalstats')
register_api(VmcpAPI, 'api_vmcp', '/vmcp')
register_api(TokenAPI, 'api_token', '/token', pk='token', pk_type='string')


@jsonpify
@blueprint.route('/app/<app_id>/newtask')
@crossdomain(origin='*', headers=cors_headers)
@ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
def new_task(app_id):
    """Return a new task for a project."""
    # Check if the request has an arg:
    try:
        task = _retrieve_new_task(app_id)
        # If there is a task for the user, return it
        if task:
            r = make_response(json.dumps(task.dictize()))
            r.mimetype = "application/json"
            return r
        else:
            return Response(json.dumps({}), mimetype="application/json")
    except Exception as e:
        return error.format_exception(e, target='app', action='GET')

def _retrieve_new_task(app_id):
    app = db.session.query(model.app.App).get(app_id)
    if app is None:
        raise NotFound
    if request.args.get('offset'):
        offset = int(request.args.get('offset'))
    else:
        offset = 0
    user_id = None if current_user.is_anonymous() else current_user.id
    user_ip = request.remote_addr if current_user.is_anonymous() else None
    task = sched.new_task(app_id, user_id, user_ip, offset)
    return task


@jsonpify
@blueprint.route('/app/<short_name>/userprogress')
@blueprint.route('/app/<int:app_id>/userprogress')
@crossdomain(origin='*', headers=cors_headers)
@ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
def user_progress(app_id=None, short_name=None):
    """API endpoint for user progress.

    Return a JSON object with two fields regarding the tasks for the user:
        { 'done': 10,
          'total: 100
        }
       This will mean that the user has done a 10% of the available tasks for
       him

    """
    if app_id or short_name:
        if short_name:
            app = _retrieve_app(short_name=short_name)
        elif app_id:
            app = _retrieve_app(app_id=app_id)
        if app:
            if current_user.is_anonymous():
                tr = db.session.query(model.task_run.TaskRun)\
                       .filter(model.task_run.TaskRun.app_id == app.id)\
                       .filter(model.task_run.TaskRun.user_ip == request.remote_addr)
            else:
                tr = db.session.query(model.task_run.TaskRun)\
                       .filter(model.task_run.TaskRun.app_id == app.id)\
                       .filter(model.task_run.TaskRun.user_id == current_user.id)
            tasks = db.session.query(model.task.Task)\
                .filter(model.task.Task.app_id == app.id)
            tmp = dict(done=tr.count(), total=tasks.count())
            return Response(json.dumps(tmp), mimetype="application/json")
        else:
            return abort(404)
    else:  # pragma: no cover
        return abort(404)


def _retrieve_app(app_id=None, short_name=None):
    if app_id != None:
        return db.session.query(model.app.App)\
                    .get(app_id)
    if short_name != None:
        return db.session.query(model.app.App)\
                    .filter(model.app.App.short_name == short_name)\
                    .first()
    return None