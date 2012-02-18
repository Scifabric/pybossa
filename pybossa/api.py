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

from flask import Blueprint, request, jsonify, abort
from flask.views import View, MethodView
from flaskext.login import current_user

from pybossa.util import jsonpify 
import pybossa.model as model
from pybossa.auth import require

blueprint = Blueprint('api', __name__)


@blueprint.route('/')
def index():
    return 'The PyBossa API'


class APIBase(MethodView):
    """
    Class to create CRUD methods for all the items: project, applications,
    tasks, etc.
    """

    @jsonpify
    def get(self, id):
        """
        Returns an item from the DB with the request.data JSON object or all the
        items if id == None

        :arg self: The class of the object to be retrieved
        :arg integer id: the ID of the object in the DB
        :returns: The JSON item/s stored in the DB
        """
        getattr(require, self.__class__.__name__.lower()).read()
        if id is None:
            items = [ x.dictize() for x in model.Session.query(self.__class__).all() ]
            return json.dumps(items)
        else:
            item = model.Session.query(self.__class__).get(id)
            if item is None:
                abort(404)
            else:
                return json.dumps(item.dictize()) 

    @jsonpify
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
        if (item == None): abort(404)
        else:
            model.Session.delete(item)
            model.Session.commit()
            return "", 204

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
    # TODO: make this better - for now just any old task ...
    task = model.new_task(app_id)
    return json.dumps(task.dictize())

