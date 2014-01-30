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
    * applications,
    * tasks and
    * task_runs

"""

import json

from flask import Blueprint, request, abort, Response, current_app, make_response
from flask.views import MethodView
from flask.ext.login import current_user
from werkzeug.exceptions import NotFound, Unauthorized, Forbidden

from pybossa.util import jsonpify, crossdomain
import pybossa.model as model
from pybossa.core import db
from pybossa.auth import require
from pybossa.hateoas import Hateoas
#from pybossa.vmcp import sign
import pybossa.vmcp
from pybossa.cache import apps as cached_apps
from pybossa.ratelimit import ratelimit
import pybossa.sched as sched
from pybossa.error import ErrorStatus
import os
from itsdangerous import URLSafeSerializer
from sqlalchemy.exc import IntegrityError

blueprint = Blueprint('api', __name__)

cors_headers = ['Content-Type', 'Authorization']

error = ErrorStatus()

@blueprint.route('/')
@crossdomain(origin='*', headers=cors_headers)
@ratelimit(limit=300, per=15*60)
def index():  # pragma: no cover
    return 'The PyBossa API'


class APIBase(MethodView):
    """
    Class to create CRUD methods for all the items: applications,
    tasks and task runs.
    """
    hateoas = Hateoas()

    def valid_args(self):
        for k in request.args.keys():
            if k not in ['api_key']:
                getattr(self.__class__, k)


    @crossdomain(origin='*', headers=cors_headers)
    def options(self):  # pragma: no cover
        return ''

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15*60)
    def get(self, id):
        """
        Returns an item from the DB with the request.data JSON object or all
        the items if id == None

        :arg self: The class of the object to be retrieved
        :arg integer id: the ID of the object in the DB
        :returns: The JSON item/s stored in the DB
        """
        try:
            getattr(require, self.__class__.__name__.lower()).read()
            if id is None:
                query = db.session.query(self.__class__)
                for k in request.args.keys():
                    if k not in ['limit', 'offset', 'api_key']:
                        # Raise an error if the k arg is not a column
                        getattr(self.__class__, k)
                        query = query.filter(getattr(self.__class__, k) == request.args[k])
                try:
                    limit = min(10000, int(request.args.get('limit')))
                except (ValueError, TypeError):
                    limit = 20

                try:
                    offset = int(request.args.get('offset'))
                except (ValueError, TypeError):
                    offset = 0

                query = query.order_by(self.__class__.id)
                query = query.limit(limit)
                query = query.offset(offset)
                items = []
                for item in query.all():
                    obj = item.dictize()
                    links, link = self.hateoas.create_links(item)
                    if links:
                        obj['links'] = links
                    if link:
                        obj['link'] = link
                    items.append(obj)
                return Response(json.dumps(items), mimetype='application/json')
            else:
                item = db.session.query(self.__class__).get(id)
                if item is None:
                    raise abort(404)
                else:
                    getattr(require, self.__class__.__name__.lower()).read(item)
                    obj = item.dictize()
                    links, link = self.hateoas.create_links(item)
                    if links:
                        obj['links'] = links
                    if link:
                        obj['link'] = link
                    return Response(json.dumps(obj), mimetype='application/json')
        except Exception as e:
            return error.format_exception(e, target=self.__class__.__name__.lower(),
                                          action='GET')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15*60)
    def post(self):
        """
        Adds an item to the DB with the request.data JSON object

        :arg self: The class of the object to be inserted
        :returns: The JSON item stored in the DB
        """
        try:
            self.valid_args()
            data = json.loads(request.data)
            # Clean HATEOAS args
            data = self.hateoas.remove_links(data)
            inst = self.__class__(**data)
            getattr(require, self.__class__.__name__.lower()).create(inst)
            self._update_object(inst)
            db.session.add(inst)
            db.session.commit()
            return json.dumps(inst.dictize())
        except Exception as e:
            return error.format_exception(e, target=self.__class__.__name__.lower(),
                                          action='POST')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15*60)
    def delete(self, id):
        """
        Deletes a single item from the DB

        :arg self: The class of the object to be deleted
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7>`_.
        """
        try:
            self.valid_args()
            inst = db.session.query(self.__class__).get(id)
            if inst is None:
                raise NotFound
            getattr(require, self.__class__.__name__.lower()).delete(inst)
            db.session.delete(inst)
            db.session.commit()
            self._refresh_cache(inst)
            return '', 204
        except Exception as e:
            return error.format_exception(e, target=self.__class__.__name__.lower(),
                                          action='DELETE')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15*60)
    def put(self, id):
        """
        Updates a single item in the DB

        :arg self: The class of the object to be updated
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6>`_.
        """
        try:
            self.valid_args()
            existing = db.session.query(self.__class__).get(id)
            if existing is None:
                raise NotFound
            getattr(require, self.__class__.__name__.lower()).update(existing)
            data = json.loads(request.data)
            # may be missing the id as we allow partial updates
            data['id'] = id
            # Clean HATEOAS args
            data = self.hateoas.remove_links(data)
            inst = self.__class__(**data)
            db.session.merge(inst)
            db.session.commit()
            self._refresh_cache(inst)
            return Response(json.dumps(inst.dictize()), 200,
                            mimetype='application/json')
        except Exception as e:
            return error.format_exception(e, target=self.__class__.__name__.lower(),
                                          action='PUT')

    def _update_object(self, data_dict):
        '''Method to be overriden in inheriting classes which wish to update
        data dict.'''
        pass

    def _refresh_cache(self, data_dict):
        '''Method to be overriden in inheriting classes which wish to refresh
        cache for given object.'''
        pass


class AppAPI(APIBase):
    __class__ = model.App

    def _refresh_cache(self, obj):
        cached_apps.delete_app(obj.short_name)

    def _update_object(self, obj):
        obj.owner = current_user


class CategoryAPI(APIBase):
    __class__ = model.Category


class TaskAPI(APIBase):
    __class__ = model.Task


class TaskRunAPI(APIBase):
    __class__ = model.TaskRun

    def _update_object(self, obj):
        """Validate the task_run object and update it with user id or ip."""
        s = URLSafeSerializer(current_app.config.get('SECRET_KEY'))
        # Get the cookie with the task signed for the current task_run
        cookie_id = 'task_run_for_task_id_%s' % obj.task_id
        task_cookie = request.cookies.get(cookie_id)
        if task_cookie is None:
            raise Unauthorized("Missing task cookie for posting"
                               " a valid task_run")
        # Load the real task from the DB
        task_cookie = s.loads(task_cookie)
        task = db.session.query(model.Task).get(task_cookie['id'])
        if ((task is None) or (task.id != obj.task_id)):  # pragma: no cover
            raise Forbidden('Invalid task_id')
        if (task.app_id != obj.app_id):
            raise Forbidden('Invalid app_id')
        if not current_user.is_anonymous():
            obj.user = current_user
        else:
            obj.user_ip = request.remote_addr
        # Check if this task_run has already been posted
        task_run = db.session.query(model.TaskRun)\
                     .filter_by(app_id=obj.app_id)\
                     .filter_by(task_id=obj.task_id)\
                     .filter_by(user=obj.user)\
                     .filter_by(user_ip=obj.user_ip)\
                     .first()
        if task_run is not None:
            raise Forbidden('You have already posted this task_run')


def register_api(view, endpoint, url, pk='id', pk_type='int'):
    view_func = view.as_view(endpoint)
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

register_api(AppAPI, 'api_app', '/app', pk='id', pk_type='int')
register_api(CategoryAPI, 'api_category', '/category', pk='id', pk_type='int')
register_api(TaskAPI, 'api_task', '/task', pk='id', pk_type='int')
register_api(TaskRunAPI, 'api_taskrun', '/taskrun', pk='id', pk_type='int')


@jsonpify
@blueprint.route('/app/<app_id>/newtask')
@crossdomain(origin='*', headers=cors_headers)
@ratelimit(limit=300, per=15*60)
def new_task(app_id):
    # Check if the request has an arg:
    try:
        app = db.session.query(model.App).get(app_id)
        if app is None:
            raise NotFound
        if request.args.get('offset'):
            offset = int(request.args.get('offset'))
        else:
            offset = 0
        user_id = None if current_user.is_anonymous() else current_user.id
        user_ip = request.remote_addr if current_user.is_anonymous() else None
        task = sched.new_task(app_id, user_id, user_ip, offset)
        # If there is a task for the user, return it

        if task:
            s = URLSafeSerializer(current_app.config.get('SECRET_KEY'))
            r = make_response(json.dumps(task.dictize()))
            r.mimetype = "application/json"
            cookie_id = 'task_run_for_task_id_%s' % task.id
            r.set_cookie(cookie_id, s.dumps(task.dictize()))
            return r

        else:
            return Response(json.dumps({}), mimetype="application/json")
    except Exception as e:
        return error.format_exception(e, target='app', action='GET')


@jsonpify
@blueprint.route('/app/<short_name>/userprogress')
@blueprint.route('/app/<int:app_id>/userprogress')
@crossdomain(origin='*', headers=cors_headers)
@ratelimit(limit=300, per=15*60)
def user_progress(app_id=None, short_name=None):
    """Return a JSON object with two fields regarding the tasks for the user:
        { 'done': 10,
          'total: 100
        }
       This will mean that the user has done a 10% of the available tasks for
       him
    """
    if app_id or short_name:
        if short_name:
            app = db.session.query(model.App)\
                    .filter(model.App.short_name == short_name)\
                    .first()
        if app_id:
            app = db.session.query(model.App)\
                    .get(app_id)

        if app:
            if current_user.is_anonymous():
                tr = db.session.query(model.TaskRun)\
                       .filter(model.TaskRun.app_id == app.id)\
                       .filter(model.TaskRun.user_ip == request.remote_addr)
            else:
                tr = db.session.query(model.TaskRun)\
                       .filter(model.TaskRun.app_id == app.id)\
                       .filter(model.TaskRun.user_id == current_user.id)
            tasks = db.session.query(model.Task)\
                .filter(model.Task.app_id == app.id)
            # Return
            tmp = dict(done=tr.count(), total=tasks.count())
            return Response(json.dumps(tmp), mimetype="application/json")
        else:
            return abort(404)
    else:  # pragma: no cover
        return abort(404)


@jsonpify
@blueprint.route('/vmcp', methods=['GET'])
@ratelimit(limit=300, per=15*60)
def vmcp():
    """VMCP support to sign CernVM requests"""
    error = dict(action=request.method,
                 status="failed",
                 status_code=None,
                 target='vmcp',
                 exception_cls='vmcp',
                 exception_msg=None)
    try:
        if current_app.config.get('VMCP_KEY'):
            pkey = current_app.root_path + '/../keys/' + current_app.config.get('VMCP_KEY')
            if not os.path.exists(pkey):
                raise IOError
        else:
            raise KeyError
        if request.args.get('cvm_salt'):
            salt = request.args.get('cvm_salt')
        else:
            raise AttributeError
        data = request.args.copy()
        signed_data = pybossa.vmcp.sign(data, salt, pkey)
        return Response(json.dumps(signed_data), 200, mimetype='application/json')

    except KeyError:
        error['status_code'] = 501
        error['exception_msg'] = "The server is not configured properly, contact the admins"
        return Response(json.dumps(error), status=error['status_code'],
                        mimetype='application/json')
    except IOError:
        error['status_code'] = 501
        error['exception_msg'] = "The server is not configured properly (private key is missing), contact the admins"
        return Response(json.dumps(error), status=error['status_code'],
                        mimetype='application/json')

    except AttributeError as e:
        error['status_code'] = 415
        error['exception_msg'] = "cvm_salt parameter is missing"
        return Response(json.dumps(error), status=error['status_code'],
                        mimetype='application/json')
    #except ValueError:
    #    error['status_code'] = 415
    #    error['exception_msg'] = "Virtual Machine parameters are missing {'cpus': 1, 'ram': 128, ...}"
    #    return Response(json.dumps(error), status=error['status_code'],
    #                    mimetype='application/json')
