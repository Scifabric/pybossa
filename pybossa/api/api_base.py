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
    * applications,
    * tasks,
    * task_runs,
    * etc.

"""
import json
from flask import request, abort, Response
from flask.views import MethodView
from werkzeug.exceptions import NotFound
from pybossa.util import jsonpify, crossdomain
from pybossa.core import db
from pybossa.auth import require
from pybossa.hateoas import Hateoas
from pybossa.ratelimit import ratelimit
from pybossa.error import ErrorStatus
import sqlalchemy


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

    def _query_filter_args(self, request):
        return dict((k, v)
                    for (k, v) in request.args.iteritems()
                    if k not in ['limit', 'offset', 'api_key', 'cols', 'group_by'])

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15 * 60)
    def get(self, id):
        """Get an object.

        Returns an item from the DB with the request.data JSON object or all
        the items if id == None

        :arg self: The class of the object to be retrieved
        :arg integer id: the ID of the object in the DB
        :returns: The JSON item/s stored in the DB

        """
        try:
            self._get()
            getattr(require, self.__class__.__name__.lower()).read()
            if id is not None:
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
            elif 'group_by' in request.args:
                cols = request.args.get('cols', 'amount').split(",")
                group_by = request.args['group_by'].split(',')
                group_by_cols = [getattr(self.__class__, key) for key in group_by]
                sum_cols = [sqlalchemy.func.sum(getattr(self.__class__, col)).label(col + "_sum") for col in cols]
                avg_cols = [sqlalchemy.func.avg(getattr(self.__class__, col)).label(col + "_avg") for col in cols]
                res_cols = sum_cols + avg_cols
                query = db.session.query(*group_by_cols + res_cols)
                for k, v in self._query_filter_args(request).iteritems():
                    # Raise an error if the k arg is not a column
                    getattr(self.__class__, k)
                    query = query.filter(getattr(self.__class__, k) == v)
                try:
                    limit = min(10000, int(request.args.get('limit')))
                except (ValueError, TypeError):
                    limit = 20

                try:
                    offset = int(request.args.get('offset'))
                except (ValueError, TypeError):
                    offset = 0

                query = query.group_by(*group_by_cols)
                query = query.order_by(*group_by_cols)
                query = query.limit(limit)
                query = query.offset(offset)
                def dictize(x):
                    return dict((key, getattr(x, key)) for key in x.keys())
                return Response(json.dumps([dictize(x) for x in query]), mimetype='application/json')
            else:
                query = db.session.query(self.__class__)
                for k, v in self._query_filter_args(request).iteritems():
                    # Raise an error if the k arg is not a column
                    getattr(self.__class__, k)
                    query = query.filter(getattr(self.__class__, k) == v)
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
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='GET')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15 * 60)
    def post(self):
        """Post an item to the DB with the request.data JSON object.

        :arg self: The class of the object to be inserted
        :returns: The JSON item stored in the DB

        """
        try:
            self._post()
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
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='POST')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15 * 60)
    def delete(self, id):
        """Delete a single item from the DB.

        :arg self: The class of the object to be deleted
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7>`_.

        """
        try:
            self._delete()
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
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='DELETE')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15 * 60)
    def put(self, id):
        """Update a single item in the DB.

        :arg self: The class of the object to be updated
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6>`_.

        """
        try:
            self._put()
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
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='PUT')

    def _get(self):
        """GET method to override."""
        pass

    def _post(self):
        """POST method to override."""
        pass

    def _put(self):
        """PUT method to override."""
        pass

    def _delete(self):
        """DELETE method to override."""
        pass

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
