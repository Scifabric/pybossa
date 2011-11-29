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

from flask import Blueprint, request, jsonify
from flask.views import View, MethodView

from pybossa.util import jsonpify
import pybossa.model as model

blueprint = Blueprint('api', __name__)


@blueprint.route('/')
def index():
    return 'The PyBossa API'


class APIBase(MethodView):
    @jsonpify
    def get(self, id):
        if id is None:
            items = [ x.dictize() for x in model.Session.query(self.__class__).all() ]
            return json.dumps(items)
        else:
            item = model.Session.query(self.__class__).get(id)
            return json.dumps(item.dictize()) 

    @jsonpify
    def post(self):
        data = json.loads(request.data)
        inst = self.__class__(**data)
        model.Session.add(inst)
        model.Session.commit()
        return json.dumps(inst.dictize())

    def delete(self, id):
        # delete a single project
        pass

    def put(self, id):
        # update a single project
        pass

class ProjectAPI(APIBase):
    __class__ = model.App

class TaskAPI(APIBase):
    __class__ = model.Task

class TaskRunAPI(APIBase):
    __class__ = model.TaskRun

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

register_api(ProjectAPI, 'api_project', '/project', pk='id', pk_type='int')
register_api(TaskAPI, 'api_task', '/task', pk='id', pk_type='int')
register_api(TaskRunAPI, 'api_taskrun', '/taskrun', pk='id', pk_type='int')
