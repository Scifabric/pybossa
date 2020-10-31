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
"""
PYBOSSA api module for exposing domain objects via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * projects,
    * categories,
    * tasks,
    * task_runs,
    * users,
    * global_stats,
    * helpingmaterial,
    * page

"""

import json
import jwt
from flask import Blueprint, request, abort, Response, make_response
from flask import current_app
from flask_login import current_user
from werkzeug.exceptions import NotFound
from pybossa.util import jsonpify, get_user_id_or_ip, fuzzyboolean
from pybossa.util import get_disqus_sso_payload
import pybossa.model as model
from pybossa.core import csrf, ratelimits, sentinel, anonymizer
from pybossa.ratelimit import ratelimit
from pybossa.cache.projects import n_tasks
import pybossa.sched as sched
from pybossa.error import ErrorStatus
from .global_stats import GlobalStatsAPI
from .task import TaskAPI
from .task_run import TaskRunAPI
from .project import ProjectAPI
from .announcement import AnnouncementAPI
from .blogpost import BlogpostAPI
from .category import CategoryAPI
from .favorites import FavoritesAPI
from .user import UserAPI
from .token import TokenAPI
from .result import ResultAPI
from .project_stats import ProjectStatsAPI
from .helpingmaterial import HelpingMaterialAPI
from .page import PageAPI
from pybossa.core import project_repo, task_repo
from pybossa.contributions_guard import ContributionsGuard
from pybossa.auth import jwt_authorize_project
from werkzeug.exceptions import MethodNotAllowed

blueprint = Blueprint('api', __name__)

error = ErrorStatus()


@blueprint.route('/')
@ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
def index():  # pragma: no cover
    """Return dummy text for welcome page."""
    return 'The %s API' % current_app.config.get('BRAND')


def register_api(view, endpoint, url, pk='id', pk_type='int'):
    """Register API endpoints.

    Registers new end points for the API using classes.

    """
    view_func = view.as_view(endpoint)
    csrf.exempt(view_func)
    blueprint.add_url_rule(url,
                           view_func=view_func,
                           defaults={pk: None},
                           methods=['GET', 'OPTIONS'])
    blueprint.add_url_rule(url,
                           view_func=view_func,
                           methods=['POST', 'OPTIONS'])
    blueprint.add_url_rule('%s/<%s:%s>' % (url, pk_type, pk),
                           view_func=view_func,
                           methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])


register_api(ProjectAPI, 'api_project', '/project', pk='oid', pk_type='int')
register_api(ProjectStatsAPI, 'api_projectstats',
             '/projectstats', pk='oid', pk_type='int')
register_api(CategoryAPI, 'api_category', '/category', pk='oid', pk_type='int')
register_api(TaskAPI, 'api_task', '/task', pk='oid', pk_type='int')
register_api(TaskRunAPI, 'api_taskrun', '/taskrun', pk='oid', pk_type='int')
register_api(ResultAPI, 'api_result', '/result', pk='oid', pk_type='int')
register_api(UserAPI, 'api_user', '/user', pk='oid', pk_type='int')
register_api(AnnouncementAPI, 'api_announcement',
             '/announcement', pk='oid', pk_type='int')
register_api(BlogpostAPI, 'api_blogpost', '/blogpost', pk='oid', pk_type='int')
register_api(HelpingMaterialAPI, 'api_helpingmaterial',
             '/helpingmaterial', pk='oid', pk_type='int')
register_api(PageAPI, 'api_page',
             '/page', pk='oid', pk_type='int')
register_api(GlobalStatsAPI, 'api_globalstats', '/globalstats',
             pk='oid', pk_type='int')
register_api(FavoritesAPI, 'api_favorites', '/favorites',
             pk='oid', pk_type='int')
register_api(TokenAPI, 'api_token', '/token', pk='token', pk_type='string')


@jsonpify
@blueprint.route('/project/<project_id>/newtask')
@ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
def new_task(project_id):
    """Return a new task for a project."""
    # Check if the request has an arg:
    try:
        tasks = _retrieve_new_task(project_id)

        if type(tasks) is Response:
            return tasks

        # If there is a task for the user, return it
        if tasks is not None:
            guard = ContributionsGuard(sentinel.master)
            for task in tasks:
                guard.stamp(task, get_user_id_or_ip())
            data = [task.dictize() for task in tasks]
            if len(data) == 0:
                response = make_response(json.dumps({}))
            elif len(data) == 1:
                response = make_response(json.dumps(data[0]))
            else:
                response = make_response(json.dumps(data))
            response.mimetype = "application/json"
            return response
        return Response(json.dumps({}), mimetype="application/json")
    except Exception as e:
        return error.format_exception(e, target='project', action='GET')


def _retrieve_new_task(project_id):

    project = project_repo.get(project_id)

    if project is None:
        raise NotFound

    if not project.allow_anonymous_contributors and current_user.is_anonymous:
        info = dict(
            error="This project does not allow anonymous contributors")
        error = [model.task.Task(info=info)]
        return error

    if request.args.get('external_uid'):
        resp = jwt_authorize_project(project,
                                     request.headers.get('Authorization'))
        if resp != True:
            return resp

    if request.args.get('limit'):
        limit = int(request.args.get('limit'))
    else:
        limit = 1

    if limit > 100:
        limit = 100

    if request.args.get('offset'):
        offset = int(request.args.get('offset'))
    else:
        offset = 0

    if request.args.get('orderby'):
        orderby = request.args.get('orderby')
    else:
        orderby = 'id'

    if request.args.get('desc'):
        desc = fuzzyboolean(request.args.get('desc'))
    else:
        desc = False

    user_id = None if current_user.is_anonymous else current_user.id
    user_ip = (anonymizer.ip(request.remote_addr or '127.0.0.1')
               if current_user.is_anonymous else None)
    external_uid = request.args.get('external_uid')
    task = sched.new_task(project_id, project.info.get('sched'),
                          user_id,
                          user_ip,
                          external_uid,
                          offset,
                          limit,
                          orderby=orderby,
                          desc=desc)
    return task


@jsonpify
@blueprint.route('/app/<short_name>/userprogress')
@blueprint.route('/project/<short_name>/userprogress')
@blueprint.route('/app/<int:project_id>/userprogress')
@blueprint.route('/project/<int:project_id>/userprogress')
@ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
def user_progress(project_id=None, short_name=None):
    """API endpoint for user progress.

    Return a JSON object with two fields regarding the tasks for the user:
        { 'done': 10,
          'total: 100
        }
       This will mean that the user has done a 10% of the available tasks for
       him

    """
    if project_id or short_name:
        if short_name:
            project = project_repo.get_by_shortname(short_name)
        elif project_id:
            project = project_repo.get(project_id)

        if project:
            # For now, keep this version, but wait until redis cache is
            # used here for task_runs too
            external_uid = request.args.get('external_uid')
            query_attrs = dict(project_id=project.id)
            if current_user.is_anonymous:
                if external_uid is None:
                    anon_ip = request.remote_addr or '127.0.0.1'
                    query_attrs['user_ip'] = anonymizer.ip(anon_ip)
                else:
                    query_attrs['external_uid'] = external_uid
            else:
                query_attrs['user_id'] = current_user.id
            taskrun_count = task_repo.count_task_runs_with(**query_attrs)
            tmp = dict(done=taskrun_count, total=n_tasks(project.id))
            return Response(json.dumps(tmp), mimetype="application/json")
        else:
            return abort(404)
    else:  # pragma: no cover
        return abort(404)


@jsonpify
@blueprint.route('/auth/project/<short_name>/token')
@ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
def auth_jwt_project(short_name):
    """Create a JWT for a project via its secret KEY."""
    project_secret_key = None
    if 'Authorization' in request.headers:
        project_secret_key = request.headers.get('Authorization')
    if project_secret_key:
        project = project_repo.get_by_shortname(short_name)
        if project and project.secret_key == project_secret_key:
            token = jwt.encode({'short_name': short_name,
                                'project_id': project.id},
                               project.secret_key, algorithm='HS256')
            return token
        else:
            return abort(404)
    else:
        return abort(403)


@jsonpify
@blueprint.route('/disqus/sso')
@ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
def get_disqus_sso_api():
    """Return remote_auth_s3 and api_key for disqus SSO."""
    try:
        if current_user.is_authenticated:
            message, timestamp, sig, pub_key = get_disqus_sso_payload(
                current_user)
        else:
            message, timestamp, sig, pub_key = get_disqus_sso_payload(None)

        if message and timestamp and sig and pub_key:
            remote_auth_s3 = "%s %s %s" % (message, sig, timestamp)
            tmp = dict(remote_auth_s3=remote_auth_s3, api_key=pub_key)
            return Response(json.dumps(tmp), mimetype='application/json')
        else:
            raise MethodNotAllowed
    except MethodNotAllowed as e:
        return error.format_exception(e, target='DISQUS_SSO', action='GET',
                                      message="Disqus keys are missing")
