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

This package adds GET, POST, PUT and DELETE methods for any class:
    * projects,
    * tasks,
    * task_runs,
    * users,
    * etc.

"""
import json
from flask import request, abort, Response
from flask.views import MethodView
from werkzeug.exceptions import NotFound, Unauthorized, Forbidden
from pybossa.util import jsonpify, crossdomain
from pybossa.core import db, ratelimits
from pybossa.auth import require
from pybossa.hateoas import Hateoas
from pybossa.ratelimit import ratelimit
from pybossa.error import ErrorStatus

from pybossa.repositories import UserRepository
from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository
user_repo = UserRepository(db)
project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)

repos = {'Task'   : {'repo': task_repo, 'filter': 'filter_tasks_by',
                     'get': 'get_task', 'save': 'save', 'update': 'update',
                     'delete': 'delete'},
        'TaskRun' : {'repo': task_repo, 'filter': 'filter_task_runs_by',
                     'get': 'get_task_run',  'save': 'save', 'update': 'update',
                     'delete': 'delete'},
        'User'    : {'repo': user_repo, 'filter': 'filter_by', 'get': 'get',
                     'save': 'save', 'update': 'update'},
        'App'     : {'repo': project_repo, 'filter': 'filter_by', 'get': 'get',
                     'save': 'save', 'update': 'update', 'delete': 'delete'},
        'Category': {'repo': project_repo, 'filter': 'filter_categories_by',
                     'get': 'get_category', 'save': 'save_category',
                     'update': 'update_category', 'delete': 'delete_category'}
        }


cors_headers = ['Content-Type', 'Authorization']

error = ErrorStatus()


class APIBase(MethodView):

    """Class to create CRUD methods."""

    hateoas = Hateoas()

    def valid_args(self):
        """Check if the domain object args are valid."""
        for k in request.args.keys():
            if k not in ['api_key']:
                getattr(self.__class__, k)

    @crossdomain(origin='*', headers=cors_headers)
    def options(self):  # pragma: no cover
        """Return '' for Options method."""
        return ''

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def get(self, id):
        """Get an object.

        Returns an item from the DB with the request.data JSON object or all
        the items if id == None

        :arg self: The class of the object to be retrieved
        :arg integer id: the ID of the object in the DB
        :returns: The JSON item/s stored in the DB

        """
        try:
            getattr(require, self.__class__.__name__.lower()).read()
            query = self._db_query(id)
            json_response = self._create_json_response(query, id)
            return Response(json_response, mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='GET')

    def _create_json_response(self, query_result, id):
        if len (query_result) == 1 and query_result[0] is None:
            raise abort(404)
        items = []
        for item in query_result:
            try:
                items.append(self._create_dict_from_model(item))
                getattr(require, self.__class__.__name__.lower()).read(item)
            except (Forbidden, Unauthorized):
                # Remove last added item, as it is 401 or 403
                items.pop() 
            except: # pragma: no cover
                raise
        if id:
            getattr(require, self.__class__.__name__.lower()).read(query_result[0])
            items = items[0]
        return json.dumps(items)

    def _create_dict_from_model(self, model):
        return self._select_attributes(self._add_hateoas_links(model))

    def _add_hateoas_links(self, item):
        obj = item.dictize()
        links, link = self.hateoas.create_links(item)
        if links:
            obj['links'] = links
        if link:
            obj['link'] = link
        return obj

    def _db_query(self, id):
        """Returns a list with the results of the query"""
        repo_info = repos[self.__class__.__name__]
        if id is None:
            limit, offset = self._set_limit_and_offset()
            results = self._filter_query(repo_info, limit, offset)
        else:
            repo = repo_info['repo']
            query_func = repo_info['get']
            results = [getattr(repo, query_func)(id)]
        return results

    def _filter_query(self, repo_info, limit, offset):
        filters = {}
        for k in request.args.keys():
            if k not in ['limit', 'offset', 'api_key']:
                # Raise an error if the k arg is not a column
                getattr(self.__class__, k)
                filters[k] = request.args[k]
        repo = repo_info['repo']
        query_func = repo_info['filter']
        filters = self._custom_filter(filters)
        results = getattr(repo, query_func)(**filters)
        return self._format_query_result(results, limit, offset)

    def _format_query_result(self, results, limit, offset):
        results = sorted(results, key=lambda item: item.id)
        results = results[offset:offset+limit]
        return results

    def _set_limit_and_offset(self):
        try:
            limit = min(100, int(request.args.get('limit')))
        except (ValueError, TypeError):
            limit = 20
        try:
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            offset = 0
        return limit, offset

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def post(self):
        """Post an item to the DB with the request.data JSON object.

        :arg self: The class of the object to be inserted
        :returns: The JSON item stored in the DB

        """
        try:
            self.valid_args()
            data = json.loads(request.data)
            inst = self._create_instance_from_request(data)
            repo = repos[self.__class__.__name__]['repo']
            save_func = repos[self.__class__.__name__]['save']
            getattr(repo, save_func)(inst)
            return json.dumps(inst.dictize())
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='POST')

    def _create_instance_from_request(self, data):
        data = self.hateoas.remove_links(data)
        inst = self.__class__(**data)
        self._update_object(inst)
        getattr(require, self.__class__.__name__.lower()).create(inst)
        return inst

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def delete(self, id):
        """Delete a single item from the DB.

        :arg self: The class of the object to be deleted
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7>`_.

        """
        try:
            self.valid_args()
            inst = self._delete_instance(id)
            self._refresh_cache(inst)
            return '', 204
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='DELETE')

    def _delete_instance(self, id):
        repo = repos[self.__class__.__name__]['repo']
        query_func = repos[self.__class__.__name__]['get']
        inst = getattr(repo, query_func)(id)
        if inst is None:
            raise NotFound
        getattr(require, self.__class__.__name__.lower()).delete(inst)
        delete_func = repos[self.__class__.__name__]['delete']
        getattr(repo, delete_func)(inst)
        return inst

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def put(self, id):
        """Update a single item in the DB.

        :arg self: The class of the object to be updated
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6>`_.

        """
        try:
            self.valid_args()
            inst = self._update_instance(id)
            self._refresh_cache(inst)
            return Response(json.dumps(inst.dictize()), 200,
                            mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='PUT')

    def _update_instance(self, id):
        repo = repos[self.__class__.__name__]['repo']
        query_func = repos[self.__class__.__name__]['get']
        existing = getattr(repo, query_func)(id)
        if existing is None:
            raise NotFound
        getattr(require, self.__class__.__name__.lower()).update(existing)
        data = json.loads(request.data)
        # may be missing the id as we allow partial updates
        data['id'] = id
        data = self.hateoas.remove_links(data)
        inst = self.__class__(**data)
        update_func = repos[self.__class__.__name__]['update']
        getattr(repo, update_func)(inst)
        return inst


    def _update_object(self, data_dict):
        """Update object.

        Method to be overriden in inheriting classes which wish to update
        data dict.

        """
        pass


    def _refresh_cache(self, data_dict):
        """Refresh cache.

        Method to be overriden in inheriting classes which wish to refresh
        cache for given object.

        """
        pass


    def _select_attributes(self, item_data):
        """Method to be overriden in inheriting classes in case it is not
        desired that every object attribute is returned by the API
        """
        return item_data


    def _custom_filter(self, query):
        """Method to be overriden in inheriting classes which wish to consider
        specific filtering criteria
        """
        return query
