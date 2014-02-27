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
from api_base import APIBase, cors_headers, error
from pybossa.model import User
import pybossa.view.stats as stats
import pybossa.cache.apps as cached_apps
import pybossa.cache.categories as cached_categories
from pybossa.util import jsonpify, crossdomain
from pybossa.ratelimit import ratelimit
from werkzeug.exceptions import MethodNotAllowed
from flask import request, abort, Response
from flask.views import MethodView
from flask.ext.login import current_user
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

    # Define private and public fields available through the API
    # (maybe should be defined in the model?)
    public_attributes = ('locale', 'name')

    def get(self, id):
        """Get a user.

        Returns a user from the DB with the request.data JSON object or all
        the users if id == None

        :arg self: The class of the object to be retrieved, in this case User
        :arg integer id: the ID of the user in the DB
        :returns: The JSON user/s stored in the DB

        """
        try:
            self._get()
            getattr(require, self.__class__.__name__.lower()).read()
            if id is None:
                query = db.session.query(self.__class__)
                for k in request.args.keys():
                    if k not in ['limit', 'offset', 'api_key']:
                        # Raise an error if the k arg is not a column
                        getattr(self.__class__, k)
                        query = query.filter(
                            getattr(self.__class__, k) == request.args[k])
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
                    if not(current_user.is_authenticated() and current_user.admin) and item.privacy_mode:
                        obj_copy = dict(obj)
                        for attribute in obj_copy:
                            if attribute not in self.public_attributes:
                                del obj[attribute]
                    items.append(obj)
                return Response(json.dumps(items), mimetype='application/json')
            else:
                item = db.session.query(self.__class__).get(id)
                if item is None:
                    raise abort(404)
                else:
                    getattr(require,
                            self.__class__.__name__.lower()).read(item)
                    obj = item.dictize()
                    links, link = self.hateoas.create_links(item)
                    if links:
                        obj['links'] = links
                    if link:
                        obj['link'] = link
                    if not (current_user.is_authenticated() and current_user.admin) and item.privacy_mode:
                        obj_copy = dict(obj)
                        for attribute in obj_copy:
                            if attribute not in self.public_attributes:
                                del obj[attribute]
                    return Response(json.dumps(obj),
                                    mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='GET')


    def _post(self):
        raise MethodNotAllowed(valid_methods=['GET'])

    def _delete(self):
        raise MethodNotAllowed(valid_methods=['GET'])

    def _put(self):
        raise MethodNotAllowed(valid_methods=['GET'])




