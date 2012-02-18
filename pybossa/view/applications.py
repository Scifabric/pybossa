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

from flask import Blueprint, request, url_for, flash, redirect, abort
from flask import render_template
from flaskext.wtf import Form, TextField, BooleanField, validators
from flaskext.login import login_required, current_user
from sqlalchemy.exc import UnboundExecutionError

import pybossa.model as model
from pybossa.util import Unique
from pybossa.auth import application as AppPerm

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
        if AppPerm.read():
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
        else:
            abort(403)
    except UnboundExecutionError:
        pass
    return render_template('/applications/list.html', bossa_apps=applications)

@blueprint.route('/new', methods=['GET', 'POST'])
def new():
    if AppPerm.create():
        form = AppForm(request.form, csrf_enabled=False)
        if request.method == 'POST' and form.validate():
            application = model.App(
                name = form.name.data,
                short_name = form.short_name.data,
                description = form.description.data,
                hidden = int(form.hidden.data),
                owner_id = current_user.id,
                )
            model.Session.add(application)
            model.Session.commit()
            flash('Application created!','success')
            return redirect('app')
        if request.method == 'POST' and not form.validate():
            flash('Please correct the errors', 'error')
        return render_template('applications/new.html', form = form)
    else:
        abort(403)

@blueprint.route('/delete/<id>')
def delete(id):
    application = model.Session.query(model.App).filter(model.App.id == id).first()
    if AppPerm.delete(application):
        try: 
            model.Session.delete(application)
            model.Session.commit()
            flash('Application deleted!', 'success')
            return redirect(url_for('account.profile'))
        except UnboundExecutionError:
            pass
    else:
        abort(403)

@blueprint.route('/update/<id>', methods=['GET', 'POST'])
def update(id):
    try:
        application = model.Session.query(model.App).filter(model.App.id == id).first()
        if AppPerm.update(application) :
            if request.method == 'GET':
                form = AppForm(obj=application, csrf_enabled=False)
                form.populate_obj(application)
                return render_template('/applications/update.html', form = form,
                                       bossa_app = application)

            if request.method == 'POST':
                form = AppForm(request.form, csrf_enabled=False)
                if form.validate():
                    new_application = model.App(
                        name = form.name.data,
                        short_name = form.short_name.data,
                        description = form.description.data,
                        hidden = form.hidden.data,
                        owner_id = current_user.id,
                        )
                    application = model.Session.query(model.App).filter(model.App.id == id).first()
                    new_application.id = application.id

                    model.Session.merge(new_application)
                    model.Session.commit()
                    flash('Application updated!', 'success')
                    return redirect(url_for('account.profile'))
                else:
                    flash('Please correct the errors', 'error')
                    return render_template('/applications/update.html', form = form, 
                                            bossa_app = application)
        else:
            abort(403)
    except UnboundExecutionError:
        pass

@blueprint.route('/<short_name>')
def app_details(short_name):
    try: # in case we have not set up database yet
        if AppPerm.read():
            application = model.Session.query(model.App).filter(model.App.short_name == short_name).first()
            if application and (application.hidden == 0 or application.owner_id == current_user.id):
                app = {
                    'name': application.name,
                    'short_name': application.short_name,
                    'description': application.description,
                    'creation': application.created[0:10],
                    'completion': application.completion_status()*100,
                    'last_active': application.last_activity()[0:10],
                    'owner_id': application.owner_id,
                    'image': 'ToDo',
                }
                if AppPerm.update(application):
                    return render_template('/applications/actions.html',
                                           bossa_app=application)
                else:
                    return render_template('/applications/app.html',
                                           bossa_app=application)
        else:
            abort(403)
    except UnboundExecutionError:
        pass
    return render_template('/applications/app.html', bossa_app=None)

@blueprint.route('/<short_name>/presenter')
def presenter(short_name):
    app = model.Session.query(model.App).filter(model.App.short_name == short_name).first()
    return render_template('/applications/presenter.html', app = app)

