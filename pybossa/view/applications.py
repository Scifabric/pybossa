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

from StringIO import StringIO
import requests
from flask import Blueprint, request, url_for, flash, redirect, abort, Response
from flask import render_template, make_response
from flaskext.wtf import Form, IntegerField, TextField, BooleanField, \
    SelectField, validators, HiddenInput, TextAreaField
from flaskext.login import login_required, current_user
from werkzeug.exceptions import HTTPException

import pybossa.model as model
from pybossa.core import db, cache
from pybossa.util import Unique, Pagination, unicode_csv_reader
from pybossa.auth import require
from pybossa.model import App
from pybossa.cache import apps as cached_apps

import json

blueprint = Blueprint('app', __name__)


class AppForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField('Name',
                     [validators.Required(),
                      Unique(db.session, model.App, model.App.name,
                             message="Name is already taken.")])
    short_name = TextField('Short Name',
                           [validators.Required(),
                            Unique(db.session, model.App, model.App.short_name,
                                   message="Short Name is already taken.")])
    description = TextField('Description',
                            [validators.Required(
                                message="You must provide a description.")])
    thumbnail = TextField('Icon Link')
    long_description = TextAreaField('Long Description')
    sched = SelectField('Task Scheduler',
                        choices=[('default', 'Default'),
                                 ('breadth_first', 'Breadth First'),
                                 ('depth_first', 'Depth First'),
                                 ('random', 'Random')],)
    hidden = BooleanField('Hide?')


class TaskPresenterForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    editor = TextAreaField('', [validators.Required()])


class BulkTaskCSVImportForm(Form):
    csv_url = TextField('URL', [validators.Required(message="You must "
                "provide a URL"), validators.URL(message="Oops! That's not a"
                " valid URL. You must provide a valid URL")])
class BulkTaskGDImportForm(Form):
    googledocs_url = TextField('URL', [validators.Required(message="You must "
                "provide a URL"), validators.URL(message="Oops! That's not a"
                " valid URL. You must provide a valid URL")])


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    if require.app.read():
        per_page = 5

        apps, count = cached_apps.get_published(page, per_page)

        pagination = Pagination(page, per_page, count)
        return render_template('/applications/index.html',
                               title="Applications",
                               apps=apps,
                               pagination=pagination)
    else:
        abort(403)


@blueprint.route('/draft', defaults={'page': 1})
@blueprint.route('/draft/page/<int:page>')
def draft(page):
    if require.app.read():
        per_page = 5

        apps, count = cached_apps.get_draft(page, per_page)

        pagination = Pagination(page, per_page, count)
        return render_template('/applications/draft.html',
                               title="Applications",
                               apps=apps,
                               count=count,
                               pagination=pagination)
    else:
        abort(403)


@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    errors = False
    if require.app.create():
        form = AppForm(request.form)
        if request.method == 'POST' and form.validate():
            info = {}
            # Add the info items
            if form.thumbnail.data:
                info['thumbnail'] = form.thumbnail.data
            if form.sched.data:
                info['sched'] = form.sched.data

            application = model.App(name=form.name.data,
                                    short_name=form.short_name.data,
                                    description=form.description.data,
                                    long_description=form.long_description.data,
                                    hidden=int(form.hidden.data),
                                    owner_id=current_user.id,
                                    info=info,)

            db.session.add(application)
            db.session.commit()
            # Clean cache
            flash('<i class="icon-ok"></i> Application created!', 'success')
            flash('<i class="icon-bullhorn"></i> You can check the '
                  '<strong><a href="https://docs.pybossa.com">Guide and '
                  ' Documentation</a></strong> for adding tasks, '
                  ' a thumbnail, using PyBossa.JS, etc.', 'info')
            return redirect('/app/' + application.short_name)
        if request.method == 'POST' and not form.validate():
            flash('Please correct the errors', 'error')
            errors = True
        return render_template('applications/new.html',
                               title="New Application",
                               form=form, errors=errors)
    else:
        abort(403)


@blueprint.route('/<short_name>/taskpresentereditor', methods=['GET', 'POST'])
@login_required
def task_presenter_editor(short_name):
    errors = False
    app = App.query.filter_by(short_name=short_name).first()
    if app:
        if require.app.update(app):
            form = TaskPresenterForm(request.form)
            if request.method == 'POST' and form.validate():
                app.info['task_presenter'] = form.editor.data
                db.session.add(app)
                db.session.commit()
                # Clean cache
                flash('<i class="icon-ok"></i> Task presenter added!', 'success')
                return redirect('/app/' + app.short_name)
            if request.method == 'POST' and not form.validate():
                flash('Please correct the errors', 'error')
                errors = True
            if request.method == 'GET':
                if app.info.get('task_presenter'):
                    form.editor.data = app.info['task_presenter']
                else:
                    form.editor.data = "<h1>Write your code here!<h1>"
                flash('Your code will be <em>automagically</em> rendered in \
                      the <strong>view section</strong>', 'info')
                return render_template('applications/task_presenter_editor.html',
                                       title="Application Task Presenter Editor",
                                       form=form, app=app, errors=errors)
        else:
            abort(403)
    else:
        abort(404)


@blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
@login_required
def delete(short_name):
    app = App.query.filter_by(short_name=short_name).first()
    if app:
        if require.app.delete(app):
            if request.method == 'GET':
                return render_template('/applications/delete.html',
                                       title="Delete Application: %s"
                                       % app.name,
                                       app=app)
            else:
                # Clean cache
                cache.delete_memoized(cached_apps.format_app, app)
                db.session.delete(app)
                db.session.commit()
                flash('Application deleted!', 'success')
                return redirect(url_for('account.profile'))
        else:
            abort(403)
    else:
        abort(404)


@blueprint.route('/<short_name>/update', methods=['GET', 'POST'])
@login_required
def update(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    if require.app.update(app):
        if request.method == 'GET':
            form = AppForm(obj=app)
            form.populate_obj(app)
            if app.info.get('thumbnail'):
                form.thumbnail.data = app.info['thumbnail']
            if app.info.get('sched'):
                for s in form.sched.choices:
                    if app.info['sched'] == s[0]:
                        form.sched.data = s[0]
                        break

            return render_template('/applications/update.html',
                                   title="Update the application: %s"
                                   % app.name,
                                   form=form,
                                   app=app)

        if request.method == 'POST':
            form = AppForm(request.form)
            if form.validate():
                if form.hidden.data:
                    hidden = 1
                else:
                    hidden = 0

                new_info = {}
                # Add the info items
                app = App.query.filter_by(short_name=short_name).first_or_404()
                if form.thumbnail.data:
                    new_info['thumbnail'] = form.thumbnail.data
                if form.sched.data:
                    new_info['sched'] = form.sched.data

                # Merge info object
                info = dict(app.info.items() + new_info.items())

                new_application = model.App(id=form.id.data,
                                            name=form.name.data,
                                            short_name=form.short_name.data,
                                            description=form.description.data,
                                            long_description=form.long_description.data,
                                            hidden=hidden,
                                            info=info,
                                            owner_id=current_user.id,)
                app = App.query.filter_by(short_name=short_name).first_or_404()
                db.session.merge(new_application)
                db.session.commit()
                flash('Application updated!', 'success')
                return redirect(url_for('.details',
                                        short_name=new_application.short_name))
            else:
                flash('Please correct the errors', 'error')
                return render_template('/applications/update.html',
                                       form=form,
                                       title="Edit the application",
                                       app=app)
    else:
        abort(403)


@blueprint.route('/<short_name>', defaults={'page': 1})
@blueprint.route('/<short_name>/<int:page>')
def details(short_name, page):
    application = db.session.query(model.App)\
                    .filter(model.App.short_name == short_name)\
                    .first()

    if application:
        try:
            require.app.read(application)
            require.app.update(application)

            return render_template('/applications/actions.html',
                                   app=application,
                                   title="Application: %s" % application.name)
        except HTTPException:
            if not application.hidden:
                return render_template('/applications/app.html',
                                       app=application,
                                       title="Application: %s" %
                                       application.name)
            else:
                return render_template('/applications/app.html', app=None)
    else:
        abort(404)


@blueprint.route('/<short_name>/import', methods=['GET', 'POST'])
def import_task(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()

    dataurl = None
    csvform = BulkTaskCSVImportForm(request.form)
    gdform = BulkTaskGDImportForm(request.form)
    if 'csv_url' in request.form and csvform.validate_on_submit():
        dataurl = csvform.csv_url.data
    elif 'googledocs_url' in request.form and gdform.validate_on_submit():
        dataurl = ''.join([gdform.googledocs_url.data, '&output=csv'])
    if dataurl:
        r = requests.get(dataurl)
        if r.status_code == 403:
            flash("Oops! It looks like you don't have permission to access"
                  " that file!", 'error')
            return render_template('/applications/import.html',
                    app=app, csvform=csvform, gdform=gdform)
        if (not 'text/plain' in r.headers['content-type'] and not 'text/csv'
                in r.headers['content-type']):
            flash("Oops! That file doesn't look like the right file.", 'error')
            return render_template('/applications/import.html',
                    app=app, csvform=csvform, gdform=gdform)
        empty = True
        csvcontent = StringIO(r.text)
        csvreader = unicode_csv_reader(csvcontent)
        # TODO: check for errors
        headers = []
        fields = set(['state', 'quorum', 'calibration', 'priority_0',
                      'n_answers'])
        field_header_index = []
        try:
            for row in csvreader:
                if not headers:
                    headers = row
                    if len(headers) != len(set(headers)):
                        flash('The file you uploaded has two headers with'
                              ' the same name.', 'error')
                        return render_template('/applications/import.html',
                            app=app, csvform=csvform, gdform=gdform)
                    field_headers = set(headers) & fields
                    for field in field_headers:
                        field_header_index.append(headers.index(field))
                else:
                    info = {}
                    task = model.Task(app=app)
                    for idx, cell in enumerate(row):
                        if idx in field_header_index:
                            setattr(task, headers[idx], cell)
                        else:
                            info[headers[idx]] = cell
                    task.info = info
                    db.session.add(task)
                    db.session.commit()
                    empty = False
            if empty:
                flash('Oops! It looks like the file is empty.', 'error')
                return render_template('/applications/import.html',
                    app=app, csvform=csvform, gdform=gdform)
            flash('Tasks imported successfully!', 'success')
            return redirect(url_for('.details', short_name=app.short_name))
        except:
            flash('Oops! Looks like there was an error with processing '
                  'that file!', 'error')
    return render_template('/applications/import.html',
            app=app, csvform=csvform, gdform=gdform)


@blueprint.route('/<short_name>/task/<int:task_id>')
def task_presenter(short_name, task_id):
    if (current_user.is_anonymous()):
        flash("Ooops! You are an anonymous user and will not get any credit "
              " for your contributions. <a href=\"" + url_for('account.signin',
              next=url_for('app.task_presenter', short_name=short_name,
                           task_id=task_id))
              + "\">Sign in now!</a>", "warning")
    app = App.query.filter_by(short_name=short_name).first_or_404()
    task = db.session.query(model.Task).get(task_id)
    if (task.app_id == app.id):
        #return render_template('/applications/presenter.html', app = app)
        # Check if the user has submitted a task before
        if (current_user.is_anonymous()):
            if not request.remote_addr:
                remote_addr = "127.0.0.1"
            else:
                remote_addr = request.remote_addr
            tr = db.session.query(model.TaskRun)\
                   .filter(model.TaskRun.task_id == task_id)\
                   .filter(model.TaskRun.app_id == app.id)\
                   .filter(model.TaskRun.user_ip == remote_addr)

        else:
            tr = db.session.query(model.TaskRun)\
                   .filter(model.TaskRun.task_id == task_id)\
                   .filter(model.TaskRun.app_id == app.id)\
                   .filter(model.TaskRun.user_id == current_user.id)

        tr = tr.first()
        if (tr is None):
            return render_template('/applications/presenter.html', app=app)
        else:
            return render_template('/applications/task/done.html', app=app)
    else:
        return render_template('/applications/task/wrong.html', app=app)


@blueprint.route('/<short_name>/presenter')
@blueprint.route('/<short_name>/newtask')
def presenter(short_name):
    app = App.query.filter_by(short_name=short_name)\
        .first_or_404()
    if app.info.get("tutorial"):
        if request.cookies.get(app.short_name + "tutorial") is None:
            if (current_user.is_anonymous()):
                flash("Ooops! You are an anonymous user and will not get any"
                      " credit for your contributions. <a href=\"" +
                      url_for('account.signin',
                              next=url_for('app.tutorial',
                                           short_name=short_name))
                      + "\">Sign in now!</a>", "warning")
            resp = make_response(render_template('/applications/tutorial.html',
                                 app=app))
            resp.set_cookie(app.short_name + 'tutorial', 'seen')
            return resp
        else:
            if (current_user.is_anonymous()):
                flash("Ooops! You are an anonymous user and will not get any"
                      "credit for your contributions. <a href=\"" +
                      url_for('account.signin',
                              next=url_for('app.presenter',
                                           short_name=short_name))
                      + "\">Sign in now!</a>", "warning")
            return render_template('/applications/presenter.html', app=app)
    else:
        if (current_user.is_anonymous()):
            flash("Ooops! You are an anonymous user and will not get any"
                  "credit for your contributions. <a href=\"" +
                  url_for('account.signin',
                          next=url_for('app.presenter',
                                       short_name=short_name))
                  + "\">Sign in now!</a>", "warning")

        return render_template('/applications/presenter.html', app=app)


@blueprint.route('/<short_name>/tutorial')
def tutorial(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    return render_template('/applications/tutorial.html', app=app)


@blueprint.route('/<short_name>/<int:task_id>/results.json')
def export(short_name, task_id):
    """Return a file with all the TaskRuns for a give Task"""
    app = db.session.query(model.App)\
            .filter(model.App.short_name == short_name)\
            .first()
    if app:
        task = db.session.query(model.Task)\
                 .filter(model.Task.id == task_id)\
                 .first()

        results = [tr.dictize() for tr in task.task_runs]
        return Response(json.dumps(results), mimetype='application/json')
    else:
        return abort(404)


@blueprint.route('/<short_name>/tasks', defaults={'page': 1})
@blueprint.route('/<short_name>/tasks/<int:page>')
def tasks(short_name, page):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    try:
        require.app.read(app)
        require.app.update(app)

        per_page = 10
        count = db.session.query(model.Task)\
                  .filter_by(app_id=app.id)\
                  .count()
        app_tasks = db.session.query(model.Task)\
                      .filter_by(app_id=app.id)\
                      .order_by(model.Task.id)\
                      .limit(per_page)\
                      .offset((page - 1) * per_page)\
                      .all()

        if not app_tasks and page != 1:
            abort(404)

        pagination = Pagination(page, per_page, count)
        return render_template('/applications/tasks.html',
                               app=app,
                               tasks=app_tasks,
                               title="Application: %s tasks" % app.name,
                               pagination=pagination)
    except HTTPException:
        if not app.hidden:
            per_page = 10
            count = db.session.query(model.Task)\
                      .filter_by(app_id=app.id)\
                      .count()
            app_tasks = db.session.query(model.Task)\
                          .filter_by(app_id=app.id)\
                          .order_by(model.Task.id)\
                          .limit(per_page)\
                          .offset((page - 1) * per_page)\
                          .all()

            if not app_tasks and page != 1:
                abort(404)

            pagination = Pagination(page, per_page, count)
            return render_template('/applications/tasks.html',
                                   app=app,
                                   tasks=app_tasks,
                                   title="Application: %s tasks" % app.name,
                                   pagination=pagination)
        else:
            return render_template('/applications/tasks.html', app=None)
