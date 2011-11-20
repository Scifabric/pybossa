import json

from flask import Blueprint, request, jsonify
from flask.views import View, MethodView

from pybossa.util import jsonpify
import pybossa.model as model

blueprint = Blueprint('api', __name__)


@blueprint.route('/')
def index():
    return 'The PyBossa API'


class ProjectAPI(MethodView):
    __class__ = model.App

    @jsonpify
    def get(self, project_id):
        if project_id is None:
            items = [ x.dictize() for x in model.Session.query(model.App).all() ]
            return json.dumps(items)
        else:
            item = model.Session.query(model.App).get(project_id)
            return json.dumps(item.dictize()) 

    @jsonpify
    def post(self):
        data = json.loads(request.data)
        inst = self.__class__(**data)
        model.Session.add(inst)
        model.Session.commit()
        return json.dumps(inst.dictize())

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
    methods=['GET']
    )
blueprint.add_url_rule('/project',
    view_func=project_view,
    methods=['POST']
    )
blueprint.add_url_rule('/project/<int:project_id>',
    view_func=project_view,
    methods=['GET', 'PUT', 'DELETE']
    )

