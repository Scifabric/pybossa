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

from flask import Blueprint, request, abort, Response, current_app
from flask.views import MethodView
from flask.ext.login import current_user
from werkzeug.exceptions import NotFound

from pybossa.util import jsonpify, crossdomain
import pybossa.model as model
from pybossa.core import db
from pybossa.auth import require
from pybossa.hateoas import Hateoas
from pybossa.vmcp import sign
from pybossa.cache import apps as cached_apps
import pybossa.sched as sched
import os

blueprint = Blueprint('api', __name__)

cors_headers = ['Content-Type', 'Authorization']


@blueprint.route('/')
@crossdomain(origin='*', headers=cors_headers)
def index():
    return 'The PyBossa API'


class APIBase(MethodView):
    """
    Class to create CRUD methods for all the items: applications,
    tasks and task runs.
    """
    hateoas = Hateoas()
    error_status = {"Forbidden": 403,
                    "NotFound": 404,
                    "Unauthorized": 401,
                    "TypeError": 415,
                    "ValueError": 415,
                    "DataError": 415,
                    "AttributeError": 415,
                    "IntegrityError": 415}

    def valid_args(self):
        for k in request.args.keys():
            if k not in ['api_key']:
                getattr(self.__class__, k)

    def format_exception(self, e, action):
        """Formats the exception to a valid JSON object"""
        exception_cls = e.__class__.__name__
        if self.error_status.get(exception_cls):
            status = self.error_status.get(exception_cls)
        else:
            status = 200
        error = dict(action=action,
                     status="failed",
                     status_code=status,
                     target=self.__class__.__name__.lower(),
                     exception_cls=exception_cls,
                     exception_msg=e.message)
        return Response(json.dumps(error), status=status,
                        mimetype='application/json')

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
                        # Raise an error if the k arg is not a column
                        getattr(self.__class__, k)
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
            else:
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
        except Exception as e:
            return self.format_exception(e, action='GET')

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    def post(self):
        """
        Adds an item to the DB with the request.data JSON object

        :arg self: The class of the object to be inserted
        :returns: The JSON item stored in the DB
        """
        try:
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
            return self.format_exception(e, action='POST')

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
        try:
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
            return self.format_exception(e, action='DELETE')

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
        try:
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
            return self.format_exception(e, 'PUT')

    def _update_object(self, data_dict):
        '''Method to be overriden in inheriting classes which wish to update
        data dict.'''
        pass

    def _refresh_cache(self, data_dict):
        '''Method to be overriden in inheriting classes which wish to refresh
        cache for given object.'''
        pass


class AppAPI(APIBase):
    __class__ = model.App

    def _refresh_cache(self, obj):
        cached_apps.delete_app(obj.short_name)

    def _update_object(self, obj):
        try:
            obj.owner = current_user
            if ((obj.name is None) or (obj.name == '') or (obj.short_name is None)
                    or (obj.short_name == '')):
                raise ValueError
        except ValueError as e:
            e.message = e.message + \
                ' App.name and App.short_name cannot be NULL or Empty'
            raise


class CategoryAPI(APIBase):
    __class__ = model.Category


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
                           methods=['GET', 'OPTIONS'])
    blueprint.add_url_rule(url,
                           view_func=view_func,
                           methods=['POST', 'OPTIONS'])
    blueprint.add_url_rule('%s/<%s:%s>' % (url, pk_type, pk),
                           view_func=view_func,
                           methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])

register_api(AppAPI, 'api_app', '/app', pk='id', pk_type='int')
register_api(CategoryAPI, 'api_category', '/category', pk='id', pk_type='int')
register_api(TaskAPI, 'api_task', '/task', pk='id', pk_type='int')
register_api(TaskRunAPI, 'api_taskrun', '/taskrun', pk='id', pk_type='int')


@jsonpify
@blueprint.route('/app/<app_id>/newtask')
@crossdomain(origin='*', headers=cors_headers)
def new_task(app_id):
    # Check if the request has an arg:
    app = AppAPI()
    res = app.get(id=app_id)
    if res.status_code == 200:
        if request.args.get('offset'):
            offset = int(request.args.get('offset'))
        else:
            offset = 0
        user_id = None if current_user.is_anonymous() else current_user.id
        user_ip = request.remote_addr if current_user.is_anonymous() else None
        task = sched.new_task(app_id, user_id, user_ip, offset)
        # If there is a task for the user, return it
        if task:
            return Response(json.dumps(task.dictize()), mimetype="application/json")
        else:
            return Response(json.dumps({}), mimetype="application/json")
    else:
        return res


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
            tmp = dict(done=len(tr), total=len(app.tasks))
            return Response(json.dumps(tmp), mimetype="application/json")
        else:
            return abort(404)
    else:
        return abort(404)


@jsonpify
@blueprint.route('/vmcp', methods=['GET'])
def vmcp():
    """VMCP support to sign CernVM requests"""
    error = dict(action=request.method,
                 status="failed",
                 status_code=None,
                 target='vmcp',
                 exception_cls='vmcp',
                 exception_msg=None)
    try:
        if current_app.config.get('VMCP_KEY'):
            pkey = current_app.root_path + '/../keys/' + current_app.config.get('VMCP_KEY')
            if not os.path.exists(pkey):
                raise IOError
        else:
            raise KeyError
        if request.args.get('cvm_salt'):
            salt = request.args.get('cvm_salt')
        else:
            raise AttributeError
        data = request.args.copy()
        signed_data = sign(data, salt, pkey)
        return Response(json.dumps(signed_data), 200, mimetype='application/json')

    except KeyError:
        error['status_code'] = 501
        error['exception_msg'] = "The server is not configured properly, contact the admins"
        return Response(json.dumps(error), status=error['status_code'],
                        mimetype='application/json')
    except IOError:
        error['status_code'] = 501
        error['exception_msg'] = "The server is not configured properly (private key is missing), contact the admins"
        return Response(json.dumps(error), status=error['status_code'],
                        mimetype='application/json')

    except AttributeError:
        error['status_code'] = 415
        error['exception_msg'] = "cvm_salt parameter is missing"
        return Response(json.dumps(error), status=error['status_code'],
                        mimetype='application/json')
    except ValueError:
        error['status_code'] = 415
        error['exception_msg'] = "Virtual Machine parameters are missing {'cpus': 1, 'ram': 128, ...}"
        return Response(json.dumps(error), status=error['status_code'],
                        mimetype='application/json')
