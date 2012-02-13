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

from flask import Blueprint, request, url_for, flash, redirect
from flask import render_template
from flaskext.wtf import Form, TextField, BooleanField, validators
from flaskext.login import login_required
from sqlalchemy.exc import UnboundExecutionError

import pybossa.model as model
from pybossa.util import Unique
from pybossa.auth.util import logged_user

blueprint = Blueprint('app', __name__)

class AppForm(Form):
    name = TextField('Name', [validators.Required(), Unique(model.Session,
                                                             model.App,
                                                             model.App.name)])
    short_name = TextField('Short Name', [validators.Required(),
                                          Unique(model.Session, model.App,
                                                 model.App.short_name)])
    description = TextField('Description', [validators.Required()])
    hidden = BooleanField('Hide?')

@blueprint.route('/')
def apps():
    applications = []
    try: # in case we have not set up database yet
        bossa_apps = model.Session.query(model.App).filter(model.App.hidden == 0)
        for bossa_app in bossa_apps:
            app = {
                'name': bossa_app.name,
                'short_name': bossa_app.short_name,
                'description': bossa_app.description[0:100],
                'creation': bossa_app.created[0:10],
                'last_active': bossa_app.last_activity()[0:10],
                'image': 'ToDo',
            }
            applications.append(app)
    except UnboundExecutionError:
        pass
    return render_template('/applications/list.html', bossa_apps=applications)

@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = AppForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        application = model.App(
            name = form.name.data,
            short_name = form.short_name.data,
            description = form.description.data,
            hidden = form.hidden.data,
            owner_id = logged_user().id,
            )
        model.Session.add(application)
        model.Session.commit()
        flash('Application created!','success')
        return redirect('app')
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('applications/new.html', form = form)

@blueprint.route('/<short_name>')
def app_details(short_name):
    try: # in case we have not set up database yet
        application = model.Session.query(model.App).filter(model.App.short_name == short_name).first()
        if application and (application.hidden == 0 or application.owner_id == logged_user().id):
            app = {
                'name': application.name,
                'short_name': application.short_name,
                'description': application.description,
                'creation': application.created[0:10],
                'completion': application.completion_status()*100,
                'last_active': application.last_activity()[0:10],
                'image': 'ToDo',
            }
            return render_template('/applications/app.html', bossa_app=app)
    except UnboundExecutionError:
        pass
    return render_template('/applications/app.html', bossa_app=None)


