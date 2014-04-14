# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

from StringIO import StringIO
from flask import Blueprint, request, url_for, flash, redirect, abort, Response, current_app
from flask import render_template, make_response
from flaskext.wtf import Form, IntegerField, DecimalField, TextField, BooleanField, \
    SelectField, validators, HiddenInput, TextAreaField
from flask.ext.login import login_required, current_user
from flask.ext.babel import lazy_gettext, gettext
from werkzeug.exceptions import HTTPException
from sqlalchemy.sql import text

import pybossa.model as model
import pybossa.stats as stats
import pybossa.validator as pb_validator

from pybossa.core import db
from pybossa.cache import ONE_DAY, ONE_HOUR
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.model.user import User
from pybossa.util import Pagination, UnicodeWriter, admin_required
from pybossa.auth import require
from pybossa.cache import apps as cached_apps
from pybossa.cache import categories as cached_cat
from pybossa.ckan import Ckan

import json
import importer
import presenter as presenter_module
import operator
import math
import requests

blueprint = Blueprint('app', __name__)


class AppForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(db.session, model.app.App, model.app.App.name,
                                          message="Name is already taken.")])
    short_name = TextField(lazy_gettext('Short Name'),
                           [validators.Required(),
                            pb_validator.NotAllowedChars(),
                            pb_validator.Unique(
                                db.session, model.app.App, model.app.App.short_name,
                                message=lazy_gettext(
                                    "Short Name is already taken."))])
    description = TextField(lazy_gettext('Description'),
                            [validators.Required(
                                message=lazy_gettext(
                                    "You must provide a description."))])
    thumbnail = TextField(lazy_gettext('Icon Link'))
    allow_anonymous_contributors = SelectField(
        lazy_gettext('Allow Anonymous Contributors'),
        choices=[('True', lazy_gettext('Yes')),
                 ('False', lazy_gettext('No'))])
    category_id = SelectField(lazy_gettext('Category'), coerce=int)
    long_description = TextAreaField(lazy_gettext('Long Description'))
    hidden = BooleanField(lazy_gettext('Hide?'))


class TaskPresenterForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    editor = TextAreaField('')


class TaskRedundancyForm(Form):
    n_answers = IntegerField(lazy_gettext('Redundancy'),
                             [validators.Required(),
                              validators.NumberRange(
                                  min=1, max=1000,
                                  message=lazy_gettext('Number of answers should be a \
                                                       value between 1 and 1,000'))])


class TaskPriorityForm(Form):
    task_ids = TextField(lazy_gettext('Task IDs'),
                         [validators.Required(),
                          pb_validator.CommaSeparatedIntegers()])

    priority_0 = DecimalField(lazy_gettext('Priority'),
                              [validators.NumberRange(
                                  min=0, max=1,
                                  message=lazy_gettext('Priority should be a \
                                                       value between 0.0 and 1.0'))])


class TaskSchedulerForm(Form):
    sched = SelectField(lazy_gettext('Task Scheduler'),
                        choices=[('default', lazy_gettext('Default')),
                                 ('breadth_first', lazy_gettext('Breadth First')),
                                 ('depth_first', lazy_gettext('Depth First')),
                                 ('random', lazy_gettext('Random'))])

class BlogpostForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    title = TextField(lazy_gettext('Title'),
                     [validators.Required(message=lazy_gettext(
                                    "You must enter a title for the post."))])
    body = TextAreaField(lazy_gettext('Body'),
                           [validators.Required(message=lazy_gettext(
                                    "You must enter some text for the post."))])


def app_title(app, page_name):
    if not app:  # pragma: no cover
        return "Application not found"
    if page_name is None:
        return "Application: %s" % (app.name)
    return "Application: %s &middot; %s" % (app.name, page_name)


def app_by_shortname(short_name):
    app = cached_apps.get_app(short_name)
    if app.id:
        # Populate CACHE with the data of the app
        return (app,
                cached_apps.n_tasks(app.id),
                cached_apps.n_task_runs(app.id),
                cached_apps.overall_progress(app.id),
                cached_apps.last_activity(app.id))

    else:
        cached_apps.delete_app(short_name)
        return abort(404)


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>/', defaults={'page': 1})
def redirect_old_featured(page):
    """DEPRECATED only to redirect old links"""
    return redirect(url_for('.index', page=page), 301)


@blueprint.route('/published/', defaults={'page': 1})
@blueprint.route('/published/<int:page>/', defaults={'page': 1})
def redirect_old_published(page):  # pragma: no cover
    """DEPRECATED only to redirect old links"""
    category = db.session.query(model.category.Category).first()
    return redirect(url_for('.app_cat_index', category=category.short_name, page=page), 301)


@blueprint.route('/draft/', defaults={'page': 1})
@blueprint.route('/draft/<int:page>/', defaults={'page': 1})
def redirect_old_draft(page):
    """DEPRECATED only to redirect old links"""
    return redirect(url_for('.draft', page=page), 301)


@blueprint.route('/category/featured/', defaults={'page': 1})
@blueprint.route('/category/featured/page/<int:page>/')
def index(page):
    """List apps in the system"""
    if cached_apps.n_featured() > 0:
        return app_index(page, cached_apps.get_featured, 'featured',
                         True, False)
    else:
        categories = cached_cat.get_all()
        cat_short_name = categories[0].short_name
        return redirect(url_for('.app_cat_index', category=cat_short_name))


def app_index(page, lookup, category, fallback, use_count):
    """Show apps of app_type"""

    per_page = current_app.config['APPS_PER_PAGE']

    apps, count = lookup(category, page, per_page)

    data = []
    for app in apps:
        data.append(dict(app=app, n_tasks=cached_apps.n_tasks(app['id']),
                         overall_progress=cached_apps.overall_progress(app['id']),
                         last_activity=app['last_activity'],
                         last_activity_raw=app['last_activity_raw']))


    if fallback and not apps:  # pragma: no cover
        return redirect(url_for('.index'))

    pagination = Pagination(page, per_page, count)
    categories = cached_cat.get_all()
    # Check for pre-defined categories featured and draft
    featured_cat = model.category.Category(name='Featured',
                                  short_name='featured',
                                  description='Featured applications')
    if category == 'featured':
        active_cat = featured_cat
    elif category == 'draft':
        active_cat = model.category.Category(name='Draft',
                                    short_name='draft',
                                    description='Draft applications')
    else:
        active_cat = db.session.query(model.category.Category)\
                       .filter_by(short_name=category).first()

    # Check if we have to add the section Featured to local nav
    if cached_apps.n_featured() > 0:
        categories.insert(0, featured_cat)
    template_args = {
        "apps": data,
        "title": gettext("Applications"),
        "pagination": pagination,
        "active_cat": active_cat,
        "categories": categories}

    if use_count:
        template_args.update({"count": count})
    return render_template('/applications/index.html', **template_args)


@blueprint.route('/category/draft/', defaults={'page': 1})
@blueprint.route('/category/draft/page/<int:page>/')
@login_required
@admin_required
def draft(page):
    """Show the Draft apps"""
    return app_index(page, cached_apps.get_draft, 'draft',
                     False, True)


@blueprint.route('/category/<string:category>/', defaults={'page': 1})
@blueprint.route('/category/<string:category>/page/<int:page>/')
def app_cat_index(category, page):
    """Show Apps that belong to a given category"""
    return app_index(page, cached_apps.get, category, False, True)


@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    require.app.create()
    form = AppForm(request.form)
    categories = db.session.query(model.category.Category).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    def respond(errors):
        return render_template('applications/new.html',
                               title=gettext("Create an Application"),
                               form=form, errors=errors)

    if request.method != 'POST':
        return respond(False)

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond(True)

    info = {}
    # Add the info items
    if form.thumbnail.data:
        info['thumbnail'] = form.thumbnail.data

    app = model.app.App(name=form.name.data,
                    short_name=form.short_name.data,
                    description=form.description.data,
                    long_description=form.long_description.data,
                    category_id=form.category_id.data,
                    allow_anonymous_contributors=form.allow_anonymous_contributors.data,
                    hidden=int(form.hidden.data),
                    owner_id=current_user.id,
                    info=info)

    #cached_apps.reset()
    db.session.add(app)
    db.session.commit()
    # Clean cache
    msg_1 = gettext('Application created!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')
    flash('<i class="icon-bullhorn"></i> ' +
          gettext('You can check the ') +
          '<strong><a href="https://docs.pybossa.com">' +
          gettext('Guide and Documentation') +
          '</a></strong> ' +
          gettext('for adding tasks, a thumbnail, using PyBossa.JS, etc.'),
          'info')
    return redirect(url_for('.settings', short_name=app.short_name))


@blueprint.route('/<short_name>/tasks/taskpresentereditor', methods=['GET', 'POST'])
@login_required
def task_presenter_editor(short_name):
    try:
        errors = False
        app, n_tasks, n_task_runs, overall_progress, last_activty = app_by_shortname(short_name)

        title = app_title(app, "Task Presenter Editor")
        require.app.read(app)
        require.app.update(app)

        form = TaskPresenterForm(request.form)
        if request.method == 'POST' and form.validate():
            db_app = db.session.query(model.app.App).filter_by(id=app.id).first()
            db_app.info['task_presenter'] = form.editor.data
            db.session.add(db_app)
            db.session.commit()
            cached_apps.delete_app(app.short_name)
            msg_1 = gettext('Task presenter added!')
            flash('<i class="icon-ok"></i> ' + msg_1, 'success')
            return redirect(url_for('.tasks', short_name=app.short_name))

        # It does not have a validation
        if request.method == 'POST' and not form.validate():  # pragma: no cover
            flash(gettext('Please correct the errors'), 'error')
            errors = True

        if app.info.get('task_presenter'):
            form.editor.data = app.info['task_presenter']
        else:
            if not request.args.get('template'):
                msg_1 = gettext('<strong>Note</strong> You will need to upload the'
                                ' tasks using the')
                msg_2 = gettext('CSV importer')
                msg_3 = gettext(' or download the app bundle and run the'
                                ' <strong>createTasks.py</strong> script in your'
                                ' computer')
                url = '<a href="%s"> %s</a>' % (url_for('app.import_task',
                                                        short_name=app.short_name), msg_2)
                msg = msg_1 + url + msg_3
                flash(msg, 'info')

                wrap = lambda i: "applications/presenters/%s.html" % i
                pres_tmpls = map(wrap, presenter_module.presenters)

                return render_template(
                    'applications/task_presenter_options.html',
                    title=title,
                    app=app,
                    presenters=pres_tmpls)

            tmpl_uri = "applications/snippets/%s.html" \
                % request.args.get('template')
            tmpl = render_template(tmpl_uri, app=app)
            form.editor.data = tmpl
            msg = 'Your code will be <em>automagically</em> rendered in \
                          the <strong>preview section</strong>. Click in the \
                          preview button!'
            flash(gettext(msg), 'info')
        return render_template('applications/task_presenter_editor.html',
                               title=title,
                               form=form,
                               app=app,
                               errors=errors)
    except HTTPException as e:
        if app.hidden:
            raise abort(403)
        else:  # pragma: no cover
            raise e


@blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
@login_required
def delete(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    try:
        title = app_title(app, "Delete")
        require.app.read(app)
        require.app.delete(app)
        if request.method == 'GET':
            return render_template('/applications/delete.html',
                                   title=title,
                                   app=app,
                                   n_tasks=n_tasks,
                                   overall_progress=overall_progress,
                                   last_activity=last_activity)
        # Clean cache
        cached_apps.delete_app(app.short_name)
        cached_apps.clean(app.id)
        app = App.query.get(app.id)
        db.session.delete(app)
        db.session.commit()
        flash(gettext('Application deleted!'), 'success')
        return redirect(url_for('account.profile'))
    except HTTPException:  # pragma: no cover
        if app.hidden:
            raise abort(403)
        else:
            raise


@blueprint.route('/<short_name>/update', methods=['GET', 'POST'])
@login_required
def update(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)

    def handle_valid_form(form):
        hidden = int(form.hidden.data)

        new_info = {}
        # Add the info items
        app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
        if form.thumbnail.data:
            new_info['thumbnail'] = form.thumbnail.data
        #if form.sched.data:
        #    new_info['sched'] = form.sched.data

        # Merge info object
        info = dict(app.info.items() + new_info.items())

        new_application = model.app.App(
            id=form.id.data,
            name=form.name.data,
            short_name=form.short_name.data,
            description=form.description.data,
            long_description=form.long_description.data,
            hidden=hidden,
            info=info,
            owner_id=app.owner_id,
            allow_anonymous_contributors=form.allow_anonymous_contributors.data,
            category_id=form.category_id.data)

        app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
        db.session.merge(new_application)
        db.session.commit()
        cached_apps.delete_app(short_name)
        cached_apps.reset()
        cached_cat.reset()
        cached_apps.get_app(new_application.short_name)
        flash(gettext('Application updated!'), 'success')
        return redirect(url_for('.details',
                                short_name=new_application.short_name))

    try:
        require.app.read(app)
        require.app.update(app)

        title = app_title(app, "Update")
        if request.method == 'GET':
            form = AppForm(obj=app)
            categories = db.session.query(model.category.Category).all()
            form.category_id.choices = [(c.id, c.name) for c in categories]
            if app.category_id is None:
                app.category_id = categories[0].id
            form.populate_obj(app)
            if app.info.get('thumbnail'):
                form.thumbnail.data = app.info['thumbnail']
            #if app.info.get('sched'):
            #    for s in form.sched.choices:
            #        if app.info['sched'] == s[0]:
            #            form.sched.data = s[0]
            #            break

        if request.method == 'POST':
            form = AppForm(request.form)
            categories = cached_cat.get_all()
            form.category_id.choices = [(c.id, c.name) for c in categories]
            if form.validate():
                return handle_valid_form(form)
            flash(gettext('Please correct the errors'), 'error')

        return render_template('/applications/update.html',
                               form=form,
                               title=title,
                               app=app)
    except HTTPException:
        if app.hidden:  # pragma: no cover
            raise abort(403)
        else:  # pragma: no cover
            raise


@blueprint.route('/<short_name>/')
def details(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)

    try:
        require.app.read(app)
        template = '/applications/app.html'
    except HTTPException:  # pragma: no cover
        if app.hidden:
            raise abort(403)
        else:
            raise

    title = app_title(app, None)

    template_args = {"app": app, "title": title,
                     "n_tasks": n_tasks,
                     "overall_progress": overall_progress,
                     "last_activity": last_activity}
    if current_app.config.get('CKAN_URL'):
        template_args['ckan_name'] = current_app.config.get('CKAN_NAME')
        template_args['ckan_url'] = current_app.config.get('CKAN_URL')
        template_args['ckan_pkg_name'] = short_name
    return render_template(template, **template_args)


@blueprint.route('/<short_name>/settings')
@login_required
def settings(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)

    title = app_title(app, "Settings")
    try:
        require.app.read(app)
        require.app.update(app)

        return render_template('/applications/settings.html',
                               app=app,
                               n_tasks=n_tasks,
                               overall_progress=overall_progress,
                               last_activity=last_activity,
                               title=title)
    except HTTPException:
        if app.hidden:  # pragma: no cover
            raise abort(403)
        else:
            raise


def compute_importer_variant_pairs(forms):
    """Return a list of pairs of importer variants. The pair-wise enumeration
    is due to UI design.
    """
    variants = reduce(operator.__add__,
                      [i.variants for i in forms.itervalues()],
                      [])
    if len(variants) % 2: # pragma: no cover
        variants.append("empty")

    prefix = "applications/tasks/"

    importer_variants = map(lambda i: "%s%s.html" % (prefix, i), variants)
    return [
        (importer_variants[i * 2], importer_variants[i * 2 + 1])
        for i in xrange(0, int(math.ceil(len(variants) / 2.0)))]


@blueprint.route('/<short_name>/tasks/import', methods=['GET', 'POST'])
@login_required
def import_task(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, "Import Tasks")
    loading_text = gettext("Importing tasks, this may take a while, wait...")
    template_args = {"title": title, "app": app, "loading_text": loading_text}
    try:
        require.app.read(app)
        require.app.update(app)
    except HTTPException:
        if app.hidden:  # pragma: no cover
            raise abort(403)
        else:
            raise

    data_handlers = dict([
        (i.template_id, (i.form_detector, i(request.form), i.form_id))
        for i in importer.importers])
    forms = [
        (i.form_id, i(request.form))
        for i in importer.importers]
    forms = dict(forms)
    template_args.update(forms)

    template_args["importer_variants"] = compute_importer_variant_pairs(forms)

    template = request.args.get('template')

    if not (template or request.method == 'POST'):
        return render_template('/applications/import_options.html',
                               **template_args)

    if template == 'gdocs':  # pragma: no cover
        mode = request.args.get('mode')
        if mode is not None:
            template_args["gdform"].googledocs_url.data = importer.googledocs_urls[mode]

    # in future, we shall pass an identifier of the form/template used,
    # which we can receive here, and use for a dictionary lookup, rather than
    # this search mechanism
    form = None
    handler = None
    for k, v in data_handlers.iteritems():
        field_id, handler, form_name = v
        if field_id in request.form:
            form = template_args[form_name]
            template = k
            break

    def render_forms():
        tmpl = '/applications/importers/%s.html' % template
        return render_template(tmpl, **template_args)

    if not (form and form.validate_on_submit()):  # pragma: no cover
        return render_forms()

    return _import_task(app, handler, form, render_forms)


def _import_task(app, handler, form, render_forms):
    try:
        empty = True
        n = 0
        n_data = 0
        for task_data in handler.tasks(form):
            n_data += 1
            task = model.task.Task(app_id=app.id)
            [setattr(task, k, v) for k, v in task_data.iteritems()]
            data = db.session.query(model.task.Task).filter_by(app_id=app.id).filter_by(info=task.info).first()
            if data is None:
                db.session.add(task)
                db.session.commit()
                n += 1
                empty = False
        if empty and n_data == 0:
            raise importer.BulkImportException(
                gettext('Oops! It looks like the file is empty.'))
        if empty and n_data > 0:
            flash(gettext('Oops! It looks like there are no new records to import.'), 'warning')

        msg = str(n) + " " + gettext('Tasks imported successfully!')
        if n == 1:
            msg = str(n) + " " + gettext('Task imported successfully!')
        flash(msg, 'success')
        cached_apps.delete_n_tasks(app.id)
        cached_apps.delete_n_task_runs(app.id)
        cached_apps.delete_overall_progress(app.id)
        cached_apps.delete_last_activity(app.id)
        return redirect(url_for('.tasks', short_name=app.short_name))
    except importer.BulkImportException, err_msg:
        flash(err_msg, 'error')
    except Exception as inst:  # pragma: no cover
        current_app.logger.error(inst)
        msg = 'Oops! Looks like there was an error with processing that file!'
        flash(gettext(msg), 'error')
    return render_forms()


@blueprint.route('/<short_name>/task/<int:task_id>')
def task_presenter(short_name, task_id):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    task = Task.query.filter_by(id=task_id).first_or_404()
    try:
        require.app.read(app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else:  # pragma: no cover
            raise

    if current_user.is_anonymous():
        if not app.allow_anonymous_contributors:
            msg = ("Oops! You have to sign in to participate in "
                   "<strong>%s</strong>"
                   "application" % app.name)
            flash(gettext(msg), 'warning')
            return redirect(url_for('account.signin',
                                    next=url_for('.presenter',
                                                 short_name=app.short_name)))
        else:
            msg_1 = gettext(
                "Ooops! You are an anonymous user and will not "
                "get any credit"
                " for your contributions.")
            next_url = url_for(
                'app.task_presenter',
                short_name=short_name,
                task_id=task_id)
            url = url_for(
                'account.signin',
                next=next_url)
            flash(msg_1 + "<a href=\"" + url + "\">Sign in now!</a>", "warning")

    title = app_title(app, "Contribute")
    template_args = {"app": app, "title": title}

    def respond(tmpl):
        return render_template(tmpl, **template_args)

    if not (task.app_id == app.id):
        return respond('/applications/task/wrong.html')

    #return render_template('/applications/presenter.html', app = app)
    # Check if the user has submitted a task before

    tr_search = db.session.query(model.task_run.TaskRun)\
                  .filter(model.task_run.TaskRun.task_id == task_id)\
                  .filter(model.task_run.TaskRun.app_id == app.id)

    if current_user.is_anonymous():
        remote_addr = request.remote_addr or "127.0.0.1"
        tr = tr_search.filter(model.task_run.TaskRun.user_ip == remote_addr)
    else:
        tr = tr_search.filter(model.task_run.TaskRun.user_id == current_user.id)

    tr_first = tr.first()
    if tr_first is None:
        return respond('/applications/presenter.html')
    else:
        return respond('/applications/task/done.html')


@blueprint.route('/<short_name>/presenter')
@blueprint.route('/<short_name>/newtask')
def presenter(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, "Contribute")
    template_args = {"app": app, "title": title}
    try:
        require.app.read(app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else:  # pragma: no cover
            raise

    if not app.allow_anonymous_contributors and current_user.is_anonymous():
        msg = "Oops! You have to sign in to participate in <strong>%s</strong> \
               application" % app.name
        flash(gettext(msg), 'warning')
        return redirect(url_for('account.signin',
                        next=url_for('.presenter', short_name=app.short_name)))

    msg = "Ooops! You are an anonymous user and will not \
           get any credit for your contributions. Sign in \
           now!"

    def respond(tmpl):
        if (current_user.is_anonymous()):
            msg_1 = gettext(msg)
            flash(msg_1, "warning")
        resp = make_response(render_template(tmpl, **template_args))
        return resp

    if app.info.get("tutorial") and \
            request.cookies.get(app.short_name + "tutorial") is None:
        resp = respond('/applications/tutorial.html')
        resp.set_cookie(app.short_name + 'tutorial', 'seen')
        return resp
    else:
        return respond('/applications/presenter.html')


@blueprint.route('/<short_name>/tutorial')
def tutorial(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, "Tutorial")
    try:
        require.app.read(app)
    except HTTPException:
        if app.hidden:
            return abort(403)
        else: # pragma: no cover
            raise
    return render_template('/applications/tutorial.html', title=title, app=app)


@blueprint.route('/<short_name>/<int:task_id>/results.json')
def export(short_name, task_id):
    """Return a file with all the TaskRuns for a give Task"""
    # Check if the app exists
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    try:
        require.app.read(app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else: # pragma: no cover
            raise

    # Check if the task belongs to the app and exists
    task = db.session.query(model.task.Task).filter_by(app_id=app.id)\
                                       .filter_by(id=task_id).first()
    if task:
        taskruns = db.session.query(model.task_run.TaskRun).filter_by(task_id=task_id)\
                             .filter_by(app_id=app.id).all()
        results = [tr.dictize() for tr in taskruns]
        return Response(json.dumps(results), mimetype='application/json')
    else:
        return abort(404)


@blueprint.route('/<short_name>/tasks/')
def tasks(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, "Tasks")
    try:
        require.app.read(app)
        return render_template('/applications/tasks.html',
                               title=title,
                               app=app,
                               n_tasks=n_tasks,
                               overall_progress=overall_progress,
                               last_activity=last_activity)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else: # pragma: no cover
            raise


@blueprint.route('/<short_name>/tasks/browse', defaults={'page': 1})
@blueprint.route('/<short_name>/tasks/browse/<int:page>')
def tasks_browse(short_name, page):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, "Tasks")

    def respond():
        per_page = 10
        count = db.session.query(model.task.Task)\
            .filter_by(app_id=app.id)\
            .count()
        app_tasks = db.session.query(model.task.Task)\
            .filter_by(app_id=app.id)\
            .order_by(model.task.Task.id)\
            .limit(per_page)\
            .offset((page - 1) * per_page)\
            .all()

        if not app_tasks and page != 1:
            abort(404)

        pagination = Pagination(page, per_page, count)
        return render_template('/applications/tasks_browse.html',
                               app=app,
                               tasks=app_tasks,
                               title=title,
                               pagination=pagination)

    try:
        require.app.read(app)
        return respond()
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else: # pragma: no cover
            raise


@blueprint.route('/<short_name>/tasks/delete', methods=['GET', 'POST'])
@login_required
def delete_tasks(short_name):
    """Delete ALL the tasks for a given application"""
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    try:
        require.app.read(app)
        require.app.update(app)
        if request.method == 'GET':
            title = app_title(app, "Delete")
            return render_template('applications/tasks/delete.html',
                                   app=app,
                                   n_tasks=n_tasks,
                                   overall_progress=overall_progress,
                                   last_activity=last_activity,
                                   title=title)
        else:
            tasks = db.session.query(model.task.Task).filter_by(app_id=app.id).all()
            for t in tasks:
                db.session.delete(t)
            db.session.commit()
            msg = gettext("All the tasks and associated task runs have been deleted")
            flash(msg, 'success')
            cached_apps.delete_last_activity(app.id)
            cached_apps.delete_n_tasks(app.id)
            cached_apps.delete_n_task_runs(app.id)
            cached_apps.delete_overall_progress(app.id)
            return redirect(url_for('.tasks', short_name=app.short_name))
    except HTTPException:
        return abort(403)


@blueprint.route('/<short_name>/tasks/export')
def export_to(short_name):
    """Export Tasks and TaskRuns in the given format"""
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, gettext("Export"))
    loading_text = gettext("Exporting data..., this may take a while")

    try:
        require.app.read(app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else: # pragma: no cover
            raise

    def respond():
        return render_template('/applications/export.html',
                               title=title,
                               loading_text=loading_text,
                               app=app)

    def gen_json(table):
        n = db.session.query(table)\
            .filter_by(app_id=app.id).count()
        sep = ", "
        yield "["
        for i, tr in enumerate(db.session.query(table)
                                 .filter_by(app_id=app.id).yield_per(1), 1):
            item = json.dumps(tr.dictize())
            if (i == n):
                sep = ""
            yield item + sep
        yield "]"

    def format_csv_properly(row):
        keys = sorted(row.keys())
        values = []
        for k in keys:
            values.append(row[k])
        return values


    def handle_task(writer, t):
        if (type(t.info) == dict):
            values = format_csv_properly(t.info)
            writer.writerow(values)
        else: # pragma: no cover
            writer.writerow([t.info])

    def handle_task_run(writer, t):
        if (type(t.info) == dict):
            values = format_csv_properly(t.info)
            writer.writerow(values)
        else: # pragma: no cover
            writer.writerow([t.info])

    def get_csv(out, writer, table, handle_row):
        for tr in db.session.query(table)\
                .filter_by(app_id=app.id)\
                .yield_per(1):
            handle_row(writer, tr)
        yield out.getvalue()

    def respond_json(ty):
        tables = {"task": model.task.Task, "task_run": model.task_run.TaskRun}
        try:
            table = tables[ty]
        except KeyError:
            return abort(404)
        return Response(gen_json(table), mimetype='application/json')

    def create_ckan_datastore(ckan, table, package_id):
        tables = {"task": model.task.Task, "task_run": model.task_run.TaskRun}
        new_resource = ckan.resource_create(name=table,
                                            package_id=package_id)
        ckan.datastore_create(name=table,
                              resource_id=new_resource['result']['id'])
        ckan.datastore_upsert(name=table,
                              records=gen_json(tables[table]),
                              resource_id=new_resource['result']['id'])

    def respond_ckan(ty):
        # First check if there is a package (dataset) in CKAN
        tables = {"task": model.task.Task, "task_run": model.task_run.TaskRun}
        msg_1 = gettext("Data exported to ")
        msg = msg_1 + "%s ..." % current_app.config['CKAN_URL']
        ckan = Ckan(url=current_app.config['CKAN_URL'],
                    api_key=current_user.ckan_api)
        app_url = url_for('.details', short_name=app.short_name, _external=True)

        try:
            package, e = ckan.package_exists(name=app.short_name)
            if e:
                raise e
            if package:
                # Update the package
                owner = User.query.get(app.owner_id)
                package = ckan.package_update(app=app, user=owner, url=app_url,
                                              resources=package['resources'])

                ckan.package = package
                resource_found = False
                # print len(package['resources'])
                for r in package['resources']:
                    if r['name'] == ty:
                        ckan.datastore_delete(name=ty, resource_id=r['id'])
                        ckan.datastore_create(name=ty, resource_id=r['id'])
                        ckan.datastore_upsert(name=ty,
                                              records=gen_json(tables[ty]),
                                              resource_id=r['id'])
                        resource_found = True
                        break
                if not resource_found:
                    create_ckan_datastore(ckan, ty, package['id'])
            else:
                owner = User.query.get(app.owner_id)
                package = ckan.package_create(app=app, user=owner, url=app_url)
                create_ckan_datastore(ckan, ty, package['id'])
                #new_resource = ckan.resource_create(name=ty,
                #                                    package_id=package['id'])
                #ckan.datastore_create(name=ty,
                #                      resource_id=new_resource['result']['id'])
                #ckan.datastore_upsert(name=ty,
                #                     records=gen_json(tables[ty]),
                #                     resource_id=new_resource['result']['id'])
            flash(msg, 'success')
            return respond()
        except requests.exceptions.ConnectionError:
                msg = "CKAN server seems to be down, try again layer or contact the CKAN admins"
                current_app.logger.error(msg)
                flash(msg, 'danger')
        except Exception as inst:
            if len(inst.args) == 3:
                t, msg, status_code = inst.args
                msg = ("Error: %s with status code: %s" % (t, status_code))
            else: # pragma: no cover
                msg = ("Error: %s" % inst.args[0])
            current_app.logger.error(msg)
            flash(msg, 'danger')
        finally:
            return respond()

    def respond_csv(ty):
        # Export Task(/Runs) to CSV
        types = {
            "task": (
                model.task.Task, handle_task,
                (lambda x: True),
                gettext(
                    "Oops, the application does not have tasks to \
                    export, if you are the owner add some tasks")),
            "task_run": (
                model.task_run.TaskRun, handle_task_run,
                (lambda x: type(x.info) == dict),
                gettext(
                    "Oops, there are no Task Runs yet to export, invite \
                     some users to participate"))}
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
                writer.writerow(sorted(t.info.keys()))

            return Response(get_csv(out, writer, table, handle_row),
                            mimetype='text/csv')
        else:
            flash(msg, 'info')
            return respond()

    export_formats = ["json", "csv"]
    if current_user.is_authenticated():
        if current_user.ckan_api:
            export_formats.append('ckan')

    ty = request.args.get('type')
    fmt = request.args.get('format')
    if not (fmt and ty):
        if len(request.args) >= 1:
            abort(404)
        return render_template('/applications/export.html',
                               title=title,
                               loading_text=loading_text,
                               ckan_name=current_app.config.get('CKAN_NAME'),
                               app=app)
    if fmt not in export_formats:
        abort(415)
    return {"json": respond_json, "csv": respond_csv, 'ckan': respond_ckan}[fmt](ty)


@blueprint.route('/<short_name>/stats')
def show_stats(short_name):
    """Returns App Stats"""
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, "Statistics")

    try:
        require.app.read(app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else: # pragma: no cover
            raise

    if not ((n_tasks > 0) and (n_task_runs > 0)):
        return render_template('/applications/non_stats.html',
                               title=title,
                               app=app)

    dates_stats, hours_stats, users_stats = stats.get_stats(
        app.id,
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


@blueprint.route('/<short_name>/tasks/settings')
@login_required
def task_settings(short_name):
    """Settings page for tasks of the application"""
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    try:
        require.app.read(app)
        require.app.update(app)
        return render_template('applications/task_settings.html',
                               app=app)
    except:  # pragma: no cover
        return abort(403)


@blueprint.route('/<short_name>/tasks/redundancy', methods=['GET', 'POST'])
@login_required
def task_n_answers(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, gettext('Redundancy'))
    form = TaskRedundancyForm()
    try:
        require.app.read(app)
        require.app.update(app)
        if request.method == 'GET':
            return render_template('/applications/task_n_answers.html',
                                   title=title,
                                   form=form,
                                   app=app)
        elif request.method == 'POST' and form.validate():
            sql = text('''
                       UPDATE task SET n_answers=:n_answers,
                       state='ongoing' WHERE app_id=:app_id''')
            db.engine.execute(sql, n_answers=form.n_answers.data, app_id=app.id)
            msg = gettext('Redundancy of Tasks updated!')
            flash(msg, 'success')
            return redirect(url_for('.tasks', short_name=app.short_name))
        else:
            flash(gettext('Please correct the errors'), 'error')
            return render_template('/applications/task_n_answers.html',
                                   title=title,
                                   form=form,
                                   app=app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else: # pragma: no cover
            raise


@blueprint.route('/<short_name>/tasks/scheduler', methods=['GET', 'POST'])
@login_required
def task_scheduler(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, gettext('Task Scheduler'))
    form = TaskSchedulerForm()

    def respond():
        return render_template('/applications/task_scheduler.html',
                               title=title,
                               form=form,
                               app=app)
    try:
        require.app.read(app)
        require.app.update(app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else: # pragma: no cover
            raise

    if request.method == 'GET':
        if app.info.get('sched'):
            for s in form.sched.choices:
                if app.info['sched'] == s[0]:
                    form.sched.data = s[0]
                    break
        return respond()

    if request.method == 'POST' and form.validate():
        app = App.query.filter_by(short_name=app.short_name).first()
        if form.sched.data:
            app.info['sched'] = form.sched.data
        db.session.add(app)
        db.session.commit()
        cached_apps.delete_app(app.short_name)
        msg = gettext("Application Task Scheduler updated!")
        flash(msg, 'success')
        return redirect(url_for('.tasks', short_name=app.short_name))
    else: # pragma: no cover
        flash(gettext('Please correct the errors'), 'error')
        return respond()


@blueprint.route('/<short_name>/tasks/priority', methods=['GET', 'POST'])
@login_required
def task_priority(short_name):
    app, n_tasks, n_task_runs, overall_progress, last_activity = app_by_shortname(short_name)
    title = app_title(app, gettext('Task Priority'))
    form = TaskPriorityForm()

    def respond():
        return render_template('/applications/task_priority.html',
                               title=title,
                               form=form,
                               app=app)
    try:
        require.app.read(app)
        require.app.update(app)
    except HTTPException:
        if app.hidden:
            raise abort(403)
        else:
            raise

    if request.method == 'GET':
        return respond()
    if request.method == 'POST' and form.validate():
        tasks = []
        for task_id in form.task_ids.data.split(","):
            if task_id != '':
                t = db.session.query(model.task.Task).filter_by(app_id=app.id)\
                              .filter_by(id=int(task_id)).first()
                if t:
                    t.priority_0 = form.priority_0.data
                    tasks.append(t)
                else:  # pragma: no cover
                    flash(gettext(("Ooops, Task.id=%s does not belong to the app" % task_id)), 'danger')
        db.session.add_all(tasks)
        db.session.commit()
        cached_apps.delete_app(app.short_name)
        flash(gettext("Task priority has been changed"), 'success')
        return respond()
    else:
        flash(gettext('Please correct the errors'), 'error')
        return respond()


@blueprint.route('/<short_name>/blog')
def show_blogposts(short_name):
    app = app_by_shortname(short_name)[0]
    blogposts = db.session.query(model.blogpost.Blogpost).filter_by(app_id=app.id).all()
    require.blogpost.read(app_id=app.id)
    return render_template('applications/blog.html', app=app, blogposts=blogposts)


@blueprint.route('/<short_name>/blog/<int:id>')
def show_blogpost(short_name, id):
    app = app_by_shortname(short_name)[0]
    blogpost = db.session.query(model.blogpost.Blogpost).filter_by(id=id,
                                                        app_id=app.id).first()
    if blogpost is None:
        raise abort(404)
    require.blogpost.read(blogpost)
    return render_template('applications/blog_post.html', blogpost=blogpost)


@blueprint.route('/<short_name>/blog/new', methods=['GET', 'POST'])
@login_required
def new_blogpost(short_name):

    def respond():
        return render_template('applications/new_blogpost.html',
                               title=gettext("Write a new post"),
                               form=form, app=app)

    app = app_by_shortname(short_name)[0]
    form = BlogpostForm(request.form)

    if request.method != 'POST':
        require.blogpost.create(app_id=app.id)
        return respond()

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond()

    blogpost = model.blogpost.Blogpost(title=form.title.data,
                                body=form.body.data,
                                user_id=current_user.id,
                                app_id=app.id)
    require.blogpost.create(blogpost)
    db.session.add(blogpost)
    db.session.commit()
    cached_apps.delete_app(short_name)

    msg_1 = gettext('Blog post created!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')

    return redirect(url_for('.show_blogposts', short_name=short_name))


@blueprint.route('/<short_name>/blog/<int:id>/update', methods=['GET', 'POST'])
def update_blogpost(short_name, id):
    app = app_by_shortname(short_name)[0]
    blogpost = db.session.query(model.blogpost.Blogpost).filter_by(id=id,
                                                        app_id=app.id).first()
    if blogpost is None:
        raise abort(404)

    def respond():
        return render_template('applications/update_blogpost.html',
                               title=gettext("Edit a post"),
                               form=form, app=app,
                               blogpost=blogpost)
    form = BlogpostForm()

    if request.method != 'POST':
        form = BlogpostForm(obj=blogpost)
        return respond()

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond()


    blogpost = model.blogpost.Blogpost(id=form.id.data,
                                title=form.title.data,
                                body=form.body.data,
                                user_id=current_user.id,
                                app_id=app.id)
    db.session.merge(blogpost)
    db.session.commit()
    cached_apps.delete_app(short_name)

    msg_1 = gettext('Blog post updated!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')

    return redirect(url_for('.show_blogposts', short_name=short_name))


@blueprint.route('/<short_name>/blog/<int:id>/delete', methods=['POST'])
def delete_blogpost(short_name, id):
    app = app_by_shortname(short_name)[0]
    blogpost = db.session.query(model.blogpost.Blogpost).filter_by(id=id,
                                                        app_id=app.id).first()
    if blogpost is None:
        raise abort(404)

    db.session.delete(blogpost)
    db.session.commit()
    cached_apps.delete_app(short_name)
    flash('<i class="icon-ok"></i> ' + 'Blog post deleted!', 'success')
    return redirect(url_for('.show_blogposts', short_name=short_name))




