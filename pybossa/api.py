import json

from flask import Blueprint, request, jsonify
from flask.views import View, MethodView

from pybossa.util import jsonpify

blueprint = Blueprint('api', __name__)


@blueprint.route('/')
def index():
    return 'The PyBossa API'

import pybossa.model as model

class ProjectAPI(MethodView):
    @jsonpify
    def get(self, project_id):
        if project_id is None:
            items = [ x.dictize() for x in model.Session.query(model.App).all() ]
            return json.dumps(items)
        else:
            item = model.Session.query(model.App).get(project_id)
            return json.dumps(item.dictize()) 

    def post(self):
        pass

    def delete(self, project_id):
        # delete a single project
        pass

    def put(self, project_id):
        # update a single project
        pass

project_view = ProjectAPI.as_view('project_api')
blueprint.add_url_rule('/project',
    view_func=project_view,
    defaults={'project_id': None},
    methods=['GET', 'POST']
    )
blueprint.add_url_rule('/project/<int:project_id>',
    view_func=project_view,
    methods=['GET', 'PUT', 'POST', 'DELETE']
    )

