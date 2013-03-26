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
from flask import Blueprint, request, url_for, flash, redirect, abort, Response, current_app
from flask import render_template, make_response
from flaskext.wtf import Form, IntegerField, TextField, BooleanField, \
    SelectField, validators, HiddenInput, TextAreaField
from flaskext.login import login_required, current_user
from werkzeug.exceptions import HTTPException

import pybossa.model as model
import pybossa.stats as stats

from pybossa.core import db
from pybossa.model import App, Task
from pybossa.util import Unique, Pagination, unicode_csv_reader, UnicodeWriter
from pybossa.auth import require
from pybossa.cache import apps as cached_apps

import json
import sys

blueprint = Blueprint('app', __name__)


class BulkImportException(Exception):
    pass


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
    allow_anonymous_contributors = SelectField('Allow Anonymous Contributors',
                                               choices=[('True', 'Yes'),
                                                        ('False', 'No')])
    long_description = TextAreaField('Long Description')
    sched = SelectField('Task Scheduler',
                        choices=[('default', 'Default'),
                                 ('breadth_first', 'Breadth First'),
                                 ('depth_first', 'Depth First'),
                                 ('random', 'Random')],)
    hidden = BooleanField('Hide?')


class TaskPresenterForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    editor = TextAreaField('')


class BulkTaskCSVImportForm(Form):
    msg_required = "You must provide a URL"
    msg_url = "Oops! That's not a valid URL. You must provide a valid URL"
    csv_url = TextField('URL',
                        [validators.Required(message=msg_required),
                         validators.URL(message=msg_url)])


class BulkTaskGDImportForm(Form):
    msg_required = "You must provide a URL"
    msg_url = "Oops! That's not a valid URL. You must provide a valid URL"
    googledocs_url = TextField('URL',
                               [validators.Required(message=msg_required),
                                   validators.URL(message=msg_url)])


class BulkTaskEpiCollectPlusImportForm(Form):
    msg_required = "You must provide an EpiCollect Plus project name"
    msg_form_required = "You must provide a Form name for the project"
    epicollect_project = TextField('Project Name',
                               [validators.Required(message=msg_required)])
    epicollect_form = TextField('Form name',
                               [validators.Required(message=msg_required)])


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    """By default show the Featured apps"""
    if require.app.read():
        per_page = 5

        apps, count = cached_apps.get_featured(page, per_page)

        if apps:
            pagination = Pagination(page, per_page, count)
            return render_template('/applications/index.html',
                                   title="Applications",
                                   apps=apps,
                                   pagination=pagination,
                                   app_type='app-featured')
        else:
            return redirect(url_for('.published'))
    else:
        abort(403)


@blueprint.route('/published', defaults={'page': 1})
@blueprint.route('/published/page/<int:page>')
def published(page):
    """Show the Published apps"""
    if require.app.read():
        per_page = 5

        apps, count = cached_apps.get_published(page, per_page)

        pagination = Pagination(page, per_page, count)
        return render_template('/applications/index.html',
                               title="Applications",
                               apps=apps,
                               count=count,
                               pagination=pagination,
                               app_type='app-published')
    else:
        abort(403)


@blueprint.route('/draft', defaults={'page': 1})
@blueprint.route('/draft/page/<int:page>')
def draft(page):
    if require.app.read():
        per_page = 5

        apps, count = cached_apps.get_draft(page, per_page)

        pagination = Pagination(page, per_page, count)
        return render_template('/applications/index.html',
                               title="Applications",
                               apps=apps,
                               count=count,
                               pagination=pagination,
                               app_type='app-draft')
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

            app = model.App(name=form.name.data,
                            short_name=form.short_name.data,
                            description=form.description.data,
                            long_description=form.long_description.data,
                            hidden=int(form.hidden.data),
                            owner_id=current_user.id,
                            info=info,)

            cached_apps.reset()
            db.session.add(app)
            db.session.commit()
            # Clean cache
            flash('<i class="icon-ok"></i> Application created!', 'success')
            flash('<i class="icon-bullhorn"></i> You can check the '
                  '<strong><a href="https://docs.pybossa.com">Guide and '
                  ' Documentation</a></strong> for adding tasks, '
                  ' a thumbnail, using PyBossa.JS, etc.', 'info')
            return redirect(url_for('.settings', short_name=app.short_name))
        if request.method == 'POST' and not form.validate():
            flash('Please correct the errors', 'error')
            errors = True
        return render_template('applications/new.html',
                               title="Create an Application",
                               form=form, errors=errors)
    else:
        abort(403)


@blueprint.route('/<short_name>/taskpresentereditor', methods=['GET', 'POST'])
@login_required
def task_presenter_editor(short_name):
    errors = False
    app = App.query.filter_by(short_name=short_name).first()
    if not app:
        abort(404)

    title = "Application: %s &middot; Task Presenter Editor" % app.name
    if not require.app.update(app):
        abort(403)

    form = TaskPresenterForm(request.form)
    if request.method == 'POST' and form.validate():
        app.info['task_presenter'] = form.editor.data
        db.session.add(app)
        db.session.commit()
        flash('<i class="icon-ok"></i> Task presenter added!', 'success')
        return redirect(url_for('.settings', short_name=app.short_name))

    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
        errors = True

    if request.method != 'GET':
        return

    if app.info.get('task_presenter'):
        form.editor.data = app.info['task_presenter']
    else:
        if request.args.get('template'):
            tmpl_uri = "applications/snippets/%s.html" \
                % request.args.get('template')
            tmpl = render_template(tmpl_uri, app=app)
            form.editor.data = tmpl
            msg = 'Your code will be <em>automagically</em> rendered in \
                      the <strong>preview section</strong>. Click in the \
                      preview button!'
            flash(msg, 'info')
        else:
            msg = '<strong>Note</strong> You will need to upload ' \
                'the tasks using the <a href="%s">' \
                'CSV importer</a> or download the app ' \
                'bundle and run the <strong>createTasks.py ' \
                '</strong> script in your ' \
                'computer' % url_for('app.import_task',
                                     short_name=app.short_name)
            flash(msg, 'info')
            return render_template(
                'applications/task_presenter_options.html',
                title=title,
                app=app)
    return render_template('applications/task_presenter_editor.html',
                           title=title,
                           form=form,
                           app=app,
                           errors=errors)


@blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
@login_required
def delete(short_name):
    app = App.query.filter_by(short_name=short_name).first()
    if app:
        title = "Application: %s &middot; Delete" % app.name
        if require.app.delete(app):
            if request.method == 'GET':
                return render_template('/applications/delete.html',
                                       title=title,
                                       app=app)
            else:
                # Clean cache
                cached_apps.clean(app.id)
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
        title = "Application: %s &middot; Update" % app.name
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
                                   title=title,
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
                                            owner_id=app.owner_id,
                                            allow_anonymous_contributors=form.allow_anonymous_contributors.data)
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
                                       title=title,
                                       app=app)
    else:
        abort(403)


@blueprint.route('/<short_name>/')
def details(short_name):
    app = db.session.query(model.App)\
                    .filter(model.App.short_name == short_name)\
                    .first()
    if app:
        title = "Application: %s" % app.name
        try:
            require.app.read(app)
            require.app.update(app)

            return render_template('/applications/actions.html',
                                   app=app,
                                   title=title)
        except HTTPException:
            if not app.hidden:
                return render_template('/applications/app.html',
                                       app=app,
                                       title=title)
            else:
                return render_template('/applications/app.html',
                                       title="Application not found",
                                       app=None)
    else:
        abort(404)


@blueprint.route('/<short_name>/settings')
@login_required
def settings(short_name):
    application = db.session.query(model.App)\
                    .filter(model.App.short_name == short_name)\
                    .first()

    if application:
        title = "Application: %s &middot; Settings" % application.name
        try:
            require.app.read(application)
            require.app.update(application)

            return render_template('/applications/settings.html',
                                   app=application,
                                   title=title)
        except HTTPException:
            return abort(403)
    else:
        abort(404)


def import_csv_tasks(app, csvreader):
    headers = []
    fields = set(['state', 'quorum', 'calibration', 'priority_0',
                  'n_answers'])
    field_header_index = []
    empty = True

    for row in csvreader:
        print row
        if not headers:
            headers = row
            if len(headers) != len(set(headers)):
                raise BulkImportException('The file you uploaded has two headers with'
                                         ' the same name.')
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
        raise BulkImportException('Oops! It looks like the file is empty.')


def import_epicollect_tasks(app, data):
    for d in data:
        task = model.Task(app=app)
        task.info = d
        db.session.add(task)
    db.session.commit()

googledocs_urls = {
    'image': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE"
             "&usp=sharing",
    'sound': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc"
             "&usp=sharing",
    'map': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc"
           "&usp=sharing",
    'pdf': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE"
           "&usp=sharing"}

def get_data_url(**kwargs):
    csvform = kwargs["csvform"]
    gdform = kwargs["gdform"]
    epiform = kwargs["epiform"]

    if 'csv_url' in request.form and csvform.validate_on_submit():
        return csvform.csv_url.data
    elif 'googledocs_url' in request.form and gdform.validate_on_submit():
        return ''.join([gdform.googledocs_url.data, '&output=csv'])
    elif 'epicollect_project' in request.form and epiform.validate_on_submit():
        return 'http://plus.epicollect.net/%s/%s.json' % \
            (epiform.epicollect_project.data, epiform.epicollect_form.data)
    else:
        return None

def get_csv_data_from_request(app, r):
    if r.status_code == 403:
        msg = "Oops! It looks like you don't have permission to access" \
            " that file"
        raise BulkImportException(msg, 'error')
    if ((not 'text/plain' in r.headers['content-type']) and
        (not 'text/csv' in r.headers['content-type'])):
        msg = "Oops! That file doesn't look like the right file."
        raise BulkImportException(msg, 'error')
    
    csvcontent = StringIO(r.text)
    csvreader = unicode_csv_reader(csvcontent)
    return import_csv_tasks(app, csvreader)

def get_epicollect_data_from_request(app, r):
    if r.status_code == 403:
        msg = "Oops! It looks like you don't have permission to access" \
            " the EpiCollect Plus project"
        raise BulkImportException(msg, 'error')
    if not 'application/json' in r.headers['content-type']:
        msg = "Oops! That project and form do not look like the right one."
        raise BulkImportException(msg, 'error')
    return import_epicollect_tasks(app, json.loads(r.text))

@blueprint.route('/<short_name>/import', methods=['GET', 'POST'])
def import_task(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    title = "Applications: %s &middot; Import Tasks" % app.name

    dataurl = None
    csvform = BulkTaskCSVImportForm(request.form)
    gdform = BulkTaskGDImportForm(request.form)
    epiform = BulkTaskEpiCollectPlusImportForm(request.form)

    template_args = {
        "title": title,
        "app": app,
        "csvform": csvform,
        "epiform": epiform,
        "gdform": gdform
        }

    if not (app.tasks or (request.args.get('template') or 
                          request.method == 'POST')):
        return render_template('/applications/import_options.html',
                               **template_args)

    template = request.args.get('template')

    if template in googledocs_urls:
        gdform.googledocs_url.data = googledocs_urls[template]

    dataurl = get_data_url(**template_args)

    def render_forms():
        tmpl = '/applications/import.html'    
        return render_template(tmpl, **template_args)

    if not dataurl:
        return render_forms()

    try:
        r = requests.get(dataurl)
        if 'csv_url' in request.form or 'googledocs_url' in request.form:
            get_data_from_request(app, r)
        elif 'epicollect_project' in request.form:
            get_epicollect_data_from_request(app, r)
        flash('Tasks imported successfully!', 'success')
        return redirect(url_for('.settings', short_name=app.short_name))
    except BulkImportException, err_msg:
        flash(err_msg, 'error')
    except Exception as inst:
        msg = 'Oops! Looks like there was an error with processing that file!'
        flash(msg, 'error')
    return render_forms()

@blueprint.route('/<short_name>/task/<int:task_id>')
def task_presenter(short_name, task_id):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    task = Task.query.filter_by(id=task_id).first_or_404()

    if not app.allow_anonymous_contributors and current_user.is_anonymous():
        msg = "Oops! You have to sign in to participate in <strong>%s</strong> \
               application" % app.name
        flash(msg, 'warning')
        return redirect(url_for('account.signin',
                        next=url_for('.presenter', short_name=app.short_name)))
    if (current_user.is_anonymous()):
        flash("Ooops! You are an anonymous user and will not get any credit "
              " for your contributions. <a href=\"" + url_for('account.signin',
              next=url_for('app.task_presenter', short_name=short_name,
                           task_id=task_id))
              + "\">Sign in now!</a>", "warning")
    if app:
        title = "Application: %s &middot; Contribute" % app.name
    else:
        title = "Application not found"

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
            return render_template('/applications/presenter.html',
                                   title=title, app=app)
        else:
            return render_template('/applications/task/done.html',
                                   title=title, app=app)
    else:
        return render_template('/applications/task/wrong.html',
                               title=title, app=app)


@blueprint.route('/<short_name>/presenter')
@blueprint.route('/<short_name>/newtask')
def presenter(short_name):
    app = App.query.filter_by(short_name=short_name)\
        .first_or_404()
    title = "Application &middot; %s &middot; Contribute" % app.name
    if not app.allow_anonymous_contributors and current_user.is_anonymous():
        msg = "Oops! You have to sign in to participate in <strong>%s</strong> \
               application" % app.name
        flash(msg, 'warning')
        return redirect(url_for('account.signin',
                        next=url_for('.presenter', short_name=app.short_name)))

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
                                                 title=title,
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
            return render_template('/applications/presenter.html',
                                   title=title,
                                   app=app)
    else:
        if (current_user.is_anonymous()):
            flash("Ooops! You are an anonymous user and will not get any"
                  "credit for your contributions. <a href=\"" +
                  url_for('account.signin',
                          next=url_for('app.presenter',
                                       short_name=short_name))
                  + "\">Sign in now!</a>", "warning")

        return render_template('/applications/presenter.html',
                               title=title,
                               app=app)


@blueprint.route('/<short_name>/tutorial')
def tutorial(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    if app:
        title = "Application: %s &middot; Tutorial" % app.name
    else:
        title = "Application not found"
    return render_template('/applications/tutorial.html', title=title, app=app)


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
    if app:
        title = "Application: %s &middot; Tasks" % app.name
    else:
        title = "Application not found"
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
                               title=title,
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
                                   title=title,
                                   pagination=pagination)
        else:
            return render_template('/applications/tasks.html',
                                   title="Application not found",
                                   app=None)


@blueprint.route('/<short_name>/tasks/delete', methods=['GET', 'POST'])
@login_required
def delete_tasks(short_name):
    """Delete ALL the tasks for a given application"""
    app = App.query.filter_by(short_name=short_name).first_or_404()
    try:
        require.app.read(app)
        require.app.update(app)
        if request.method == 'GET':
            title = "Application Tasks: %s &middot; Delete" % app.name
            return render_template('applications/tasks/delete.html',
                                   app=app,
                                   title=title)
        else:
            for task in app.tasks:
                db.session.delete(task)
            db.session.commit()
            msg = "All the tasks and associated task runs have been deleted"
            flash(msg, 'success')
            return redirect(url_for('.settings', short_name=app.short_name))
    except HTTPException:
        return abort(403)


@blueprint.route('/<short_name>/export')
def export_to(short_name):
    """Export Tasks and TaskRuns in the given format"""
    app = App.query.filter_by(short_name=short_name).first_or_404()
    if app:
        title = "Application: %s &middot; Export" % app.name
    else:
        title = "Application not found"

    def gen_json(table):
        n = db.session.query(table)\
            .filter_by(app_id=app.id).count()
        sep = ", "
        yield "["
        for i, tr in enumerate(db.session.query(table)\
                .filter_by(app_id=app.id).yield_per(1), 1):
            item = json.dumps(tr.dictize())
            if (i == n):
                sep = ""
            yield item + sep
        yield "]"

    def handle_task(writer, t):
        writer.writerow(t.info.values())

    def handle_task_run(writer, t):
        if (type(t.info) == dict):
            writer.writerow(t.info.values())
        else:
            writer.writerow([t.info])

    def get_csv(out, writer, table, handle_row):
        for tr in db.session.query(table)\
                .filter_by(app_id=app.id)\
                .yield_per(1):
            handle_row(writer, tr)
        yield out.getvalue()

    ty = request.args.get('type')
    fmt = request.args.get('format')
    if fmt and ty:
        if fmt not in ["json", "csv"]:
            abort(404)
        if fmt == 'json':
            tables = {"task": model.Task, "task_run": model.TaskRun}
            try:
                table = tables[ty]
            except KeyError:
                return abort(404)
            return Response(gen_json(table), mimetype='application/json')
        elif fmt == 'csv':
            # Export Task(/Runs) to CSV
            types = {
                "task": (
                    model.Task, handle_task,
                    (lambda x: True),
                    "Oops, the application does not have tasks to \
                           export, if you are the owner add some tasks"),
                "task_run": (
                    model.TaskRun, handle_task_run,
                    (lambda x: type(x.info) == dict),
                    "Oops, there are no Task Runs yet to export, invite \
                           some users to participate")
                }
            try:
                table, handle_row, test, msg = types[ty]
            except KeyError:
                return abort(404)

            out = StringIO()
            writer = UnicodeWriter(out)
            t = db.session.query(table)\
                .filter_by(app_id=app.id)\
                .first()
            if t is not None:
                if test(t):
                    writer.writerow(t.info.keys())

                return Response(get_csv(out, writer, table, handle_row), 
                                mimetype='text/csv')
            else:
                flash(msg, 'info')
                return render_template('/applications/export.html',
                                       title=title,
                                       app=app)
    elif len(request.args) >= 1:
        abort(404)
    else:
        return render_template('/applications/export.html',
                               title=title,
                               app=app)


@blueprint.route('/<short_name>/stats')
def show_stats(short_name):
    """Returns App Stats"""
    app = db.session.query(model.App).filter_by(short_name=short_name).first()
    title = "Application: %s &middot; Statistics" % app.name
    if len(app.tasks) > 0 and len(app.task_runs) > 0:
        dates_stats, hours_stats, users_stats = stats.get_stats(app.id,
                                                                current_app.config['GEO'])
        anon_pct_taskruns = int((users_stats['n_anon'] * 100) /
                                (users_stats['n_anon'] + users_stats['n_auth']))
        userStats = dict(
            geo=current_app.config['GEO'],
            anonymous=dict(
                users=users_stats['n_anon'],
                taskruns=users_stats['n_anon'],
                pct_taskruns=anon_pct_taskruns,
                top5=users_stats['anon']['top5']),
            authenticated=dict(
                users=users_stats['n_auth'],
                taskruns=users_stats['n_auth'],
                pct_taskruns=100 - anon_pct_taskruns,
                top5=users_stats['auth']['top5']))

        tmp = dict(userStats=users_stats['users'],
                   userAnonStats=users_stats['anon'],
                   userAuthStats=users_stats['auth'],
                   dayStats=dates_stats,
                   hourStats=hours_stats)

        return render_template('/applications/stats.html',
                               title=title,
                               appStats=json.dumps(tmp),
                               userStats=userStats,
                               app=app)
    else:
        return render_template('/applications/non_stats.html',
                               title=title,
                               app=app)
