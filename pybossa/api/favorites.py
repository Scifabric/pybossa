# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
PYBOSSA api module for Favorites via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * Task favorites

"""
import json
from .api_base import APIBase
from pybossa.core import task_repo
from flask_login import current_user
from flask import Response, abort, request
from werkzeug.exceptions import MethodNotAllowed, NotFound, Unauthorized
from pybossa.core import ratelimits
from pybossa.util import jsonpify, fuzzyboolean
from pybossa.ratelimit import ratelimit
from pybossa.error import ErrorStatus
from pybossa.model.task import Task

error = ErrorStatus()


class FavoritesAPI(APIBase):

    """Class API for Favorites."""

    __class__ = Task

    @jsonpify
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def get(self, oid):
        """Return all the tasks favorited by current user."""
        try:
            if current_user.is_anonymous:
                raise abort(401)
            uid = current_user.id
            limit, offset, orderby = self._set_limit_and_offset()
            last_id = request.args.get('last_id')
            print(last_id)
            desc = request.args.get('desc') if request.args.get('desc') else False
            desc = fuzzyboolean(desc)

            tasks = task_repo.filter_tasks_by_user_favorites(uid, limit=limit,
                                                             offset=offset,
                                                             orderby=orderby,
                                                             desc=desc,
                                                             last_id=last_id)
            data = self._create_json_response(tasks, oid)
            return Response(data, 200,
                            mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='GET')

    @jsonpify
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def post(self):
        """Add User ID to task as a favorite."""
        try:
            self.valid_args()
            data = json.loads(request.data)
            if (len(list(data.keys())) != 1) or ('task_id' not in list(data.keys())):
                raise AttributeError
            if current_user.is_anonymous:
                raise Unauthorized
            uid = current_user.id
            tasks = task_repo.get_task_favorited(uid, data['task_id'])
            if len(tasks) == 1:
                task = tasks[0]
            if len(tasks) == 0:
                task = task_repo.get_task(data['task_id'])
                if task is None:
                    raise NotFound
                if task.fav_user_ids is None:
                    task.fav_user_ids = [uid]
                else:
                    task.fav_user_ids.append(uid)
                task_repo.update(task)
                self._log_changes(None, task)
            return Response(json.dumps(task.dictize()), 200,
                            mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='POST')

    @jsonpify
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def delete(self, oid):
        """Delete User ID from task as a favorite."""
        try:
            if current_user.is_anonymous:
                raise abort(401)
            uid = current_user.id
            tasks = task_repo.get_task_favorited(uid, oid)
            if tasks == []:
                raise NotFound
            if len(tasks) == 1:
                task = tasks[0]
            idx = task.fav_user_ids.index(uid)
            task.fav_user_ids.pop(idx)
            task_repo.update(task)
            return Response(json.dumps(task.dictize()), 200,
                            mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='DEL')

    @jsonpify
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def put(self, oid):
        try:
            raise MethodNotAllowed
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='PUT')
