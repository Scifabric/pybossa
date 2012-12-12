# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

import json

from flask import Blueprint, request, jsonify, abort, Response
from flask.views import View, MethodView
from flaskext.login import current_user
from sqlalchemy.exc import DatabaseError

from pybossa.util import jsonpify, crossdomain
import pybossa.model as model
from pybossa.core import db
from pybossa.auth import require
import pybossa.sched as sched

blueprint = Blueprint('api', __name__)

cors_headers = ['Content-Type', 'Authorization']


@blueprint.route('/')
@crossdomain(origin='*', headers=cors_headers)
def index():
    return 'The PyBossa API'


class APIBase(MethodView):
    """
    Class to create CRUD methods for all the items: project, applications,
    tasks, etc.
    """

    @crossdomain(origin='*', headers=cors_headers)
    def options(self):
        return ''

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
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
                        if not hasattr(self.__class__, k):
                            return Response(json.dumps({
                                'error': 'no such column: %s' % k}
                                ), mimetype='application/json')
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
                items = [x.dictize() for x in query.all()]
                return Response(json.dumps(items), mimetype='application/json')
            else:
                item = db.session.query(self.__class__).get(id)
                if item is None:
                    abort(404)
                else:
                    return Response(json.dumps(item.dictize()),
                            mimetype='application/json')
        #except ProgrammingError, e:
        except DatabaseError as e:
            return Response(json.dumps({'error': "%s" % e.orig}),
                    mimetype='application/json')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    def post(self):
        """
        Adds an item to the DB with the request.data JSON object

        :arg self: The class of the object to be inserted
        :returns: The JSON item stored in the DB
        """
        data = json.loads(request.data)
        inst = self.__class__(**data)
        getattr(require, self.__class__.__name__.lower()).create(inst)
        self._update_object(inst)
        db.session.add(inst)
        db.session.commit()
        return json.dumps(inst.dictize())

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    def delete(self, id):
        """
        Deletes a single item from the DB

        :arg self: The class of the object to be deleted
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7>`_.
        """
        item = db.session.query(self.__class__).get(id)
        getattr(require, self.__class__.__name__.lower()).delete(item)
        if (item is None):
            abort(404)
        else:
            db.session.delete(item)
            db.session.commit()
            return "", 204

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    def put(self, id):
        """
        Updates a single item in the DB

        :arg self: The class of the object to be updated
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action.

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6>`_.
        """
        existing = db.session.query(self.__class__).get(id)
        getattr(require, self.__class__.__name__.lower()).update(existing)
        data = json.loads(request.data)
        # may be missing the id as we allow partial updates
        data['id'] = id
        inst = self.__class__(**data)
        if (existing is None):
            abort(404)
        else:
            db.session.merge(inst)
            db.session.commit()
            return "", 200

    def _update_object(self, data_dict):
        '''Method to be overriden in inheriting classes which wish to update
        data dict.'''
        pass


class ProjectAPI(APIBase):
    __class__ = model.App

    def _update_object(self, obj):
        obj.owner = current_user


class TaskAPI(APIBase):
    __class__ = model.Task


class TaskRunAPI(APIBase):
    __class__ = model.TaskRun

    def _update_object(self, obj):
        if not current_user.is_anonymous():
            obj.user = current_user
        else:
            obj.user_ip = request.remote_addr


def register_api(view, endpoint, url, pk='id', pk_type='int'):
    view_func = view.as_view(endpoint)
    blueprint.add_url_rule(url,
        view_func=view_func,
        defaults={pk: None},
        methods=['GET', 'OPTIONS']
        )
    blueprint.add_url_rule(url,
        view_func=view_func,
        methods=['POST', 'OPTIONS']
        )
    blueprint.add_url_rule('%s/<%s:%s>' % (url, pk_type, pk),
        view_func=view_func,
        methods=['GET', 'PUT', 'DELETE', 'OPTIONS']
        )

register_api(ProjectAPI, 'api_app', '/app', pk='id', pk_type='int')
register_api(TaskAPI, 'api_task', '/task', pk='id', pk_type='int')
register_api(TaskRunAPI, 'api_taskrun', '/taskrun', pk='id', pk_type='int')


@jsonpify
@blueprint.route('/app/<app_id>/newtask')
@crossdomain(origin='*', headers=cors_headers)
def new_task(app_id):
    # Check if the request has an arg:
    if request.args.get('offset'):
        offset = int(request.args.get('offset'))
    else:
        offset = 0

    user_id = None if current_user.is_anonymous() else current_user.id
    user_ip = request.remote_addr if current_user.is_anonymous() else None
    task = sched.new_task(app_id, user_id, user_ip, offset)
    # If there is a task for the user, return it
    if task:
        return Response(json.dumps(task.dictize()),
                mimetype="application/json")
    else:
        return Response(json.dumps({}), mimetype="application/json")


@jsonpify
@blueprint.route('/app/<short_name>/userprogress')
@blueprint.route('/app/<int:app_id>/userprogress')
@crossdomain(origin='*', headers=cors_headers)
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
                        .filter(model.TaskRun.user_ip == request.remote_addr)\
                        .all()
            else:
                tr = db.session.query(model.TaskRun)\
                        .filter(model.TaskRun.app_id == app.id)\
                        .filter(model.TaskRun.user_id == current_user.id)\
                        .all()
            # Return
            tmp = dict(
                    done=len(tr),
                    total=len(app.tasks)
                    )
            return Response(json.dumps(tmp), mimetype="application/json")
        else:
            return abort(404)
    else:
        return abort(404)
