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
from pybossa.auth import require
from pybossa.sched import get_default_task, get_random_task

blueprint = Blueprint('api', __name__)

@blueprint.route('/')
@crossdomain(origin='*')
def index():
    return 'The PyBossa API'


class APIBase(MethodView):
    """
    Class to create CRUD methods for all the items: project, applications,
    tasks, etc.
    """

    @jsonpify
    @crossdomain(origin='*')
    def get(self, id):
        """
        Returns an item from the DB with the request.data JSON object or all the
        items if id == None

        :arg self: The class of the object to be retrieved
        :arg integer id: the ID of the object in the DB
        :returns: The JSON item/s stored in the DB
        """
        try:
            getattr(require, self.__class__.__name__.lower()).read()
            if id is None:
                query = model.Session.query(self.__class__)
                limit = False
                for k in request.args.keys():
                    if k == 'limit':
                        limit = True
                    if k != 'limit' and k != 'api_key' and request.args[k] != '':
                        query = query.filter("%s = '%s'" % (k, request.args[k]))
                if limit:
                    query = query.limit(int(request.args['limit']))
                else:
                    # By default limit all queries to 20 records
                    query = query.limit(20)
                items = [ x.dictize() for x in query.all() ]
                return Response(json.dumps(items), mimetype='application/json')
            else:
                item = model.Session.query(self.__class__).get(id)
                if item is None:
                    abort(404)
                else:
                    return Response(json.dumps(item.dictize()), mimetype='application/json')
        #except ProgrammingError, e:
        except DatabaseError as e:
            return Response(json.dumps({'error': "%s" % e.orig}), mimetype='application/json')

    @jsonpify
    @crossdomain(origin='*')
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
        model.Session.add(inst)
        model.Session.commit()
        return json.dumps(inst.dictize())

    @jsonpify
    @crossdomain(origin='*')
    def delete(self, id):
        """
        Deletes a single item from the DB

        :arg self: The class of the object to be deleted
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action. 

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.7>`_.
        """
        item = model.Session.query(self.__class__).get(id)
        getattr(require, self.__class__.__name__.lower()).delete(item)
        if (item == None): abort(404)
        else:
            model.Session.delete(item)
            model.Session.commit()
            return "", 204

    @jsonpify
    @crossdomain(origin='*')
    def put(self, id):
        """
        Updates a single item in the DB

        :arg self: The class of the object to be updated
        :arg integer id: the ID of the object in the DB
        :returns: An HTTP status code based on the output of the action. 

        More info about HTTP status codes for this action `here
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6>`_.
        """
        existing = model.Session.query(self.__class__).get(id)
        getattr(require, self.__class__.__name__.lower()).update(existing)
        data = json.loads(request.data)
        # may be missing the id as we allow partial updates
        data['id'] = id
        inst = self.__class__(**data)
        if (existing == None):
            abort(404)
        else:
            out = model.Session.merge(inst)
            model.Session.commit()
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
        methods=['GET']
        )
    blueprint.add_url_rule(url,
        view_func=view_func,
        methods=['POST']
        )
    blueprint.add_url_rule('%s/<%s:%s>' % (url, pk_type, pk),
        view_func=view_func,
        methods=['GET', 'PUT', 'DELETE']
        )

register_api(ProjectAPI, 'api_app', '/app', pk='id', pk_type='int')
register_api(TaskAPI, 'api_task', '/task', pk='id', pk_type='int')
register_api(TaskRunAPI, 'api_taskrun', '/taskrun', pk='id', pk_type='int')

@jsonpify
@blueprint.route('/app/<app_id>/newtask')
def new_task(app_id):
    # First check which SCHED scheme has to use this app
    app = model.Session.query(model.App).get(app_id)
    if (app.info.get('sched')):
        sched = app.info['sched']
    else:
        sched = 'default'
    # Now get a task using the app sched
    if sched == 'default':
        print "%s uses the %s scheduler" % (app.name,sched)
        if current_user.is_anonymous():
            task = get_default_task(app_id,user_ip=request.remote_addr)
        else:
            task = get_default_task(app_id, user_id=current_user.id)

    if sched == 'random':
        # print "%s uses the %s scheduler" % (app.name,sched)
        if current_user.is_anonymous():
            task = get_random_task(app_id,user_ip=request.remote_addr)
        else:
            task = get_random_task(app_id, user_id=current_user.id)

    # If there is a task for the user, return it
    if task:
        return Response(json.dumps(task.dictize()), mimetype="application/json")
    else:
        return Response(json.dumps({}), mimetype="application/json")
