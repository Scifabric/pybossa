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

from flask import Blueprint
from flask import render_template
from flask import request
from flaskext.login import login_required

import pybossa.model as model
from pybossa.util import admin_required
import json


blueprint = Blueprint('admin', __name__)


@blueprint.route('/featured')
@blueprint.route('/featured/<int:app_id>', methods=['POST', 'DELETE'])
@login_required
@admin_required
def featured(app_id=None):
    """List featured apps of PyBossa"""
    if request.method == 'GET':
        apps = model.Session.query(model.App).all()
        featured = model.Session.query(model.Featured).all()
        return render_template('/admin/applications.html', apps=apps,
                featured=featured)
    if request.method == 'POST':
        f = model.Featured()
        f.app_id = app_id
        # Check if the app is already in this table
        tmp = model.Session.query(model.Featured)\
                .filter(model.Featured.app_id == app_id)\
                .first()
        if (tmp == None): 
            model.Session.add(f)
            model.Session.commit()
            return json.dumps(f.dictize())
        else:
            return json.dumps({'error': 'App.id %s already in Featured table' % app_id})
    if request.method == 'DELETE':
        f = model.Session.query(model.Featured)\
                .filter(model.Featured.app_id == app_id)\
                .first()
        if (f):
            model.Session.delete(f)
            model.Session.commit()
            return "", 204
        else:
            return json.dumps({'error': 'App.id %s is not in Featured table' % app_id})
