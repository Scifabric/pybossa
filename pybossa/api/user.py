# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
PyBossa api module for domain object USER via an API.

This package adds GET method for:
    * users

"""
import json
from api_base import APIBase, cors_headers
from pybossa.model import User
from flask import Response
import pybossa.view.stats as stats
import pybossa.cache.apps as cached_apps
import pybossa.cache.categories as cached_categories
from pybossa.util import jsonpify, crossdomain
from pybossa.ratelimit import ratelimit
from werkzeug.exceptions import MethodNotAllowed
from flask import request, abort, Response
from flask.views import MethodView
from werkzeug.exceptions import NotFound
from pybossa.util import jsonpify, crossdomain
from pybossa.core import db
from pybossa.auth import require
from pybossa.hateoas import Hateoas
from pybossa.ratelimit import ratelimit
from pybossa.error import ErrorStatus


class UserAPI(APIBase):

    """
    Class for the domain object User.

    """

    __class__ = User


    # @jsonpify
    # @crossdomain(origin='*', headers=cors_headers)
    # @ratelimit(limit=300, per=15 * 60)
    # def get(self, id):
    #     """Return global stats."""
    #     n_pending_tasks = stats.n_total_tasks_site() - stats.n_task_runs_site()
    #     n_users = stats.n_auth_users() + stats.n_anon_users()
    #     n_projects = cached_apps.n_published() + cached_apps.n_draft()
    #     data = dict(n_projects=n_projects,
    #                 n_users=n_users,
    #                 n_task_runs=stats.n_task_runs_site(),
    #                 n_pending_tasks=n_pending_tasks,
    #                 categories=[])
    #     # Add Categories
    #     categories = cached_categories.get_used()
    #     for c in categories:
    #         datum = dict()
    #         datum[c['short_name']] = cached_apps.n_count(c['short_name'])
    #         data['categories'].append(datum)
    #     # Add Featured
    #     datum = dict()
    #     datum['featured'] = cached_apps.n_featured()
    #     data['categories'].append(datum)
    #     # Add Draft
    #     datum = dict()
    #     datum['draft'] = cached_apps.n_draft()
    #     data['categories'].append(datum)
    #     return Response(json.dumps(data), 200, mimetype='application/json')

    #     try:
    #         self._get()
    #         getattr(require, self.__class__.__name__.lower()).read()
    #         if id is None:
    #             query = db.session.query(self.__class__)
    #             for k in request.args.keys():
    #                 if k not in ['limit', 'offset', 'api_key']:
    #                     # Raise an error if the k arg is not a column
    #                     getattr(self.__class__, k)
    #                     query = query.filter(
    #                         getattr(self.__class__, k) == request.args[k])
    #             try:
    #                 limit = min(10000, int(request.args.get('limit')))
    #             except (ValueError, TypeError):
    #                 limit = 20

    #             try:
    #                 offset = int(request.args.get('offset'))
    #             except (ValueError, TypeError):
    #                 offset = 0

    #             query = query.order_by(self.__class__.id)
    #             query = query.limit(limit)
    #             query = query.offset(offset)
    #             items = []
    #             for item in query.all():
    #                 obj = item.dictize()
    #                 links, link = self.hateoas.create_links(item)
    #                 if links:
    #                     obj['links'] = links
    #                 if link:
    #                     obj['link'] = link
    #                 items.append(obj)
    #             return Response(json.dumps(items), mimetype='application/json')
    #         else:
    #             item = db.session.query(self.__class__).get(id)
    #             if item is None:
    #                 raise abort(404)
    #             else:
    #                 getattr(require,
    #                         self.__class__.__name__.lower()).read(item)
    #                 obj = item.dictize()
    #                 links, link = self.hateoas.create_links(item)
    #                 if links:
    #                     obj['links'] = links
    #                 if link:
    #                     obj['link'] = link
    #                 return Response(json.dumps(obj),
    #                                 mimetype='application/json')
    #     except Exception as e:
    #         return error.format_exception(
    #             e,
    #             target=self.__class__.__name__.lower(),
    #             action='GET')

    # def _post(self):
    #     raise MethodNotAllowed

