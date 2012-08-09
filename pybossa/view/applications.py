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

from flask import Blueprint, request, url_for, flash, redirect, abort, Response
from flask import render_template
from flaskext.wtf import Form, IntegerField, TextField, BooleanField, \
                         validators, HiddenInput, TextAreaField
from flaskext.login import login_required, current_user
from sqlalchemy.exc import UnboundExecutionError
from werkzeug.exceptions import HTTPException

import pybossa.model as model
from pybossa.util import Unique
from pybossa.auth import require

import json

blueprint = Blueprint('app', __name__)


class AppForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField('Name', [validators.Required(),
                              Unique(
                                  model.Session,
                                  model.App,
                                  model.App.name,
                                  message="Name is already taken.")])
    short_name = TextField('Short Name', [validators.Required(),
                                          Unique(
                                              model.Session,
                                              model.App,
                                              model.App.short_name,
                                              message="Short Name is already \
                                                      taken.")
                                          ])
    description = TextField('Description', [validators.Required(
                                                        message="You must \
                                                                provide a \
                                                                description.")
                                           ])
    long_description = TextAreaField('Long Description')
    hidden = BooleanField('Hide?')


@blueprint.route('/')
def index():
    if require.app.read():
        apps = model.Session.query(model.App).filter(model.App.hidden == 0)
        apps_with_tasks = []
        apps_without_tasks = []
        for a in apps:
            if (len(a.tasks) > 0):
                apps_with_tasks.append(a)
            else:
                apps_without_tasks.append(a)

        return render_template('/applications/index.html', \
                                title="Applications",
                                apps_with_tasks=apps_with_tasks,
                                apps_without_tasks=apps_without_tasks)
    else:
        abort(403)


@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if require.app.create():
        form = AppForm(request.form, csrf_enabled=False)
        if request.method == 'POST' and form.validate():
            application = model.App(
                name=form.name.data,
                short_name=form.short_name.data,
                description=form.description.data,
                long_description=form.long_description.data,
                hidden=int(form.hidden.data),
                owner_id=current_user.id,
                )
            model.Session.add(application)
            model.Session.commit()
            flash('<i class="icon-ok"></i> Application created!', 'success')
            flash('<i class="icon-bullhorn"></i> You can check the '\
                   '<strong><a href="https://docs.pybossa.com">Guide and '\
                   ' Documentation</a></strong> for adding tasks, '\
                   ' a thumbnail, using PyBossa.JS, etc.', 'info')
            return redirect('/app/' + application.short_name)
        if request.method == 'POST' and not form.validate():
            flash('Please correct the errors', 'error')
        return render_template('applications/new.html', \
                title="New Application", form=form)
    else:
        abort(403)


@blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
@login_required
def delete(short_name):
    application = model.Session.query(model.App)\
            .filter(model.App.short_name == short_name).first()
    if require.app.delete(application):
            if request.method == 'GET':
                return render_template('/applications/delete.html',
                                        title="Delete Application: %s"\
                                              % application.name,
                                        app=application)
            else:
                try:
                    model.Session.delete(application)
                    model.Session.commit()
                    flash('Application deleted!', 'success')
                    return redirect(url_for('account.profile'))
                except UnboundExecutionError:
                    pass
    else:
        abort(403)


@blueprint.route('/<short_name>/update', methods=['GET', 'POST'])
@login_required
def update(short_name):
    try:
        application = model.Session.query(model.App)\
                .filter(model.App.short_name == short_name).first()
        if require.app.update(application):
            if request.method == 'GET':
                form = AppForm(obj=application, csrf_enabled=False)
                form.populate_obj(application)
                return render_template('/applications/update.html',
                                        title="Update the application: %s"\
                                               % application.name,
                                        form=form,
                                        app=application)

            if request.method == 'POST':
                form = AppForm(request.form, csrf_enabled=False)
                if form.validate():
                    if form.hidden.data:
                        hidden = 1
                    else:
                        hidden = 0
                    new_application = model.App(
                        id=form.id.data,
                        name=form.name.data,
                        short_name=form.short_name.data,
                        description=form.description.data,
                        long_description=form.long_description.data,
                        hidden=hidden,
                        owner_id=current_user.id,
                        )
                    application = model.Session.query(model.App)\
                            .filter(model.App.short_name == short_name).first()
                    model.Session.merge(new_application)
                    model.Session.commit()
                    flash('Application updated!', 'success')
                    return redirect(url_for('.details',\
                            short_name=new_application.short_name))
                else:
                    flash('Please correct the errors', 'error')
                    return render_template('/applications/update.html',\
                                            form=form,
                                            title="Edit the application",
                                            app=application)
        else:
            abort(403)
    except UnboundExecutionError:
        pass


@blueprint.route('/<short_name>')
def details(short_name):
    application = model.Session.query(model.App).\
            filter(model.App.short_name == short_name).\
            first()

    if application:
        try:
            #: Short tasks based
            completed_tasks = []
            wip_tasks = []
            for t in application.tasks:
                if t.pct_status() * 100 >= 100:
                    completed_tasks.append(t)
                else:
                    wip_tasks.append(t)

            require.app.read(application)
            require.app.update(application)
            return render_template('/applications/actions.html',
                                    title="Application: %s" % application.name,
                                    app=application,
                                    completed_tasks=completed_tasks,
                                    wip_tasks=wip_tasks)
        except HTTPException:
            # This exception is raised because the user is not authenticated or
            # it has not privileges to edit/delte the application
            if application.hidden == 0:
                return render_template('/applications/app.html',
                                    title="Application: %s" % application.name,
                                    app=application,
                                    completed_tasks=completed_tasks,
                                    wip_tasks=wip_tasks)
            else:
                return render_template('/applications/app.html', app=None)
    else:
        return abort(404)
        #return render_template('/applications/app.html', app=None)


@blueprint.route('/<short_name>/task/<int:task_id>')
def task_presenter(short_name, task_id):
    if (current_user.is_anonymous()):
        flash("Ooops! You are an anonymous user and will not get any credit "\
              " for your contributions. Sign in now!", "warning")
    app = model.Session.query(model.App)\
            .filter(model.App.short_name == short_name).first()
    task = model.Session.query(model.Task).get(task_id)
    if (task.app_id == app.id):
        #return render_template('/applications/presenter.html', app = app)
        # Check if the user has submitted a task before
        if (current_user.is_anonymous()):
            if not request.remote_addr:
                remote_addr = "127.0.0.1"
            else:
                remote_addr = request.remote_addr
            tr = model.Session.query(model.TaskRun)\
                    .filter(model.TaskRun.task_id == task_id)\
                    .filter(model.TaskRun.app_id == app.id)\
                    .filter(model.TaskRun.user_ip == remote_addr)

        else:
            tr = model.Session.query(model.TaskRun)\
                    .filter(model.TaskRun.task_id == task_id)\
                    .filter(model.TaskRun.app_id == app.id)\
                    .filter(model.TaskRun.user_id == current_user.id)

        tr = tr.first()
        if (tr == None):
            return render_template('/applications/presenter.html', app=app)
        else:
            return render_template('/applications/task/done.html', app=app)
    else:
        return render_template('/applications/task/wrong.html', app=app)


@blueprint.route('/<short_name>/presenter')
@blueprint.route('/<short_name>/newtask')
def presenter(short_name):
    if (current_user.is_anonymous()):
        flash("Ooops! You are an anonymous user and will not get any credit"\
              " for your contributions. Sign in now!", "warning")
    app = model.Session.query(model.App)\
            .filter(model.App.short_name == short_name).first()
    return render_template('/applications/presenter.html', app=app)


@blueprint.route('/<short_name>/<int:task_id>/results.json')
def export(short_name, task_id):
    """Return a file with all the TaskRuns for a give Task"""
    task = model.Session.query(model.Task)\
            .filter(model.Task.id == task_id)\
            .first()

    results = [tr.dictize() for tr in task.task_runs]
    return Response(json.dumps(results), mimetype='application/json')


#@blueprint.route('/featured')
#def featured():
#    """List featured apps of PyBossa"""
#    apps = model.Session.query(model.App)\
#            .filter(model.App.featured == 1)\
#            .all()
#    return render_template('/applications/featured.html', apps=apps)
