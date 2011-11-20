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

project_view = ProjectAPI.as_view('project_api')
blueprint.add_url_rule('/project',
    view_func=project_view,
    defaults={'id': None},
    methods=['GET']
    )
blueprint.add_url_rule('/project',
    view_func=project_view,
    methods=['POST']
    )
blueprint.add_url_rule('/project/<int:id>',
    view_func=project_view,
    methods=['GET', 'PUT', 'DELETE']
    )

