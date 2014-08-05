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

import time
import re
import json
import pybossa.importers as importer
import operator
import math
import requests
from StringIO import StringIO

from flask import Blueprint, request, url_for, flash, redirect, abort, Response, current_app
from flask import render_template, make_response
from flask.ext.login import login_required, current_user
from flask.ext.babel import gettext
from sqlalchemy.sql import text

import pybossa.model as model
import pybossa.stats as stats
import pybossa.sched as sched

from pybossa.core import db, uploader, signer, get_session
from pybossa.cache import ONE_DAY, ONE_HOUR
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.model.user import User
from pybossa.util import Pagination, UnicodeWriter, admin_required, get_user_id_or_ip
from pybossa.auth import require
from pybossa.cache import apps as cached_apps
from pybossa.cache import categories as cached_cat
from pybossa.cache.helpers import add_custom_contrib_button_to
from pybossa.ckan import Ckan
from pybossa.extensions import misaka
from pybossa.cookies import CookieHandler
from pybossa.password_manager import ProjectPasswdManager

from pybossa.forms import *


blueprint = Blueprint('app', __name__)



def app_title(app, page_name):
    if not app:  # pragma: no cover
        return "Project not found"
    if page_name is None:
        return "Project: %s" % (app.name)
    return "Project: %s &middot; %s" % (app.name, page_name)


def app_by_shortname(short_name):
    app = cached_apps.get_app(short_name)
    if app:
        # Get owner
        owner = User.query.get(app.owner_id)
        # Populate CACHE with the data of the app
        return (app,
                owner,
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
                         last_activity_raw=app['last_activity_raw'],
                         n_completed_tasks=cached_apps.n_completed_tasks(app['id']),
                         n_volunteers=cached_apps.n_volunteers(app['id'])))


    if fallback and not apps:  # pragma: no cover
        return redirect(url_for('.index'))

    pagination = Pagination(page, per_page, count)
    categories = cached_cat.get_all()
    # Check for pre-defined categories featured and draft
    featured_cat = model.category.Category(name='Featured',
                                  short_name='featured',
                                  description='Featured projects')
    if category == 'featured':
        active_cat = featured_cat
    elif category == 'draft':
        active_cat = model.category.Category(name='Draft',
                                    short_name='draft',
                                    description='Draft projects')
    else:
        active_cat = db.session.query(model.category.Category)\
                       .filter_by(short_name=category).first()

    # Check if we have to add the section Featured to local nav
    if cached_apps.n_featured() > 0:
        categories.insert(0, featured_cat)
    template_args = {
        "apps": data,
        "title": gettext("Projects"),
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

    def respond(errors):
        return render_template('applications/new.html',
                               title=gettext("Create a Project"),
                               form=form, errors=errors)

    def _description_from_long_description():
        long_desc = form.long_description.data
        html_long_desc = misaka.render(long_desc)[:-1]
        remove_html_tags_regex = re.compile('<[^>]*>')
        blank_space_regex = re.compile('\n')
        text_desc = remove_html_tags_regex.sub("", html_long_desc)[:255]
        if len(text_desc) >= 252:
            text_desc = text_desc[:-3]
            text_desc += "..."
        return blank_space_regex.sub(" ", text_desc)

    if request.method != 'POST':
        return respond(False)

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond(True)

    info = {}
    category_by_default = cached_cat.get_all()[0]

    app = model.app.App(name=form.name.data,
                    short_name=form.short_name.data,
                    description=_description_from_long_description(),
                    long_description=form.long_description.data,
                    owner_id=current_user.id,
                    info=info,
                    category_id=category_by_default.id)

    db.session.add(app)
    db.session.commit()

    msg_1 = gettext('Project created!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')
    flash('<i class="icon-bullhorn"></i> ' +
          gettext('You can check the ') +
          '<strong><a href="https://docs.pybossa.com">' +
          gettext('Guide and Documentation') +
          '</a></strong> ' +
          gettext('for adding tasks, a thumbnail, using PyBossa.JS, etc.'),
          'info')
    return redirect(url_for('.update', short_name=app.short_name))


@blueprint.route('/<short_name>/tasks/taskpresentereditor', methods=['GET', 'POST'])
@login_required
def task_presenter_editor(short_name):
    errors = False
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)

    title = app_title(app, "Task Presenter Editor")
    require.app.read(app)
    require.app.update(app)

    form = TaskPresenterForm(request.form)
    form.id.data = app.id
    if request.method == 'POST' and form.validate():
        app = App.query.get(app.id)
        app.info['task_presenter'] = form.editor.data
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
            msg_3 = gettext(' or download the project bundle and run the'
                            ' <strong>createTasks.py</strong> script in your'
                            ' computer')
            url = '<a href="%s"> %s</a>' % (url_for('app.import_task',
                                                    short_name=app.short_name), msg_2)
            msg = msg_1 + url + msg_3
            flash(msg, 'info')

            wrap = lambda i: "applications/presenters/%s.html" % i
            pres_tmpls = map(wrap, current_app.config.get('PRESENTERS'))

            app = add_custom_contrib_button_to(app, get_user_id_or_ip())
            return render_template(
                'applications/task_presenter_options.html',
                title=title,
                app=app,
                owner=owner,
                overall_progress=overall_progress,
                n_tasks=n_tasks,
                n_task_runs=n_task_runs,
                last_activity=last_activity,
                n_completed_tasks=cached_apps.n_completed_tasks(app.get('id')),
                n_volunteers=cached_apps.n_volunteers(app.get('id')),
                presenters=pres_tmpls)

        tmpl_uri = "applications/snippets/%s.html" \
            % request.args.get('template')
        tmpl = render_template(tmpl_uri, app=app)
        form.editor.data = tmpl
        msg = 'Your code will be <em>automagically</em> rendered in \
                      the <strong>preview section</strong>. Click in the \
                      preview button!'
        flash(gettext(msg), 'info')
    app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    return render_template('applications/task_presenter_editor.html',
                           title=title,
                           form=form,
                           app=app,
                           owner=owner,
                           overall_progress=overall_progress,
                           n_tasks=n_tasks,
                           n_task_runs=n_task_runs,
                           last_activity=last_activity,
                           n_completed_tasks=cached_apps.n_completed_tasks(app.get('id')),
                           n_volunteers=cached_apps.n_volunteers(app.get('id')),
                           errors=errors)


@blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
@login_required
def delete(short_name):
    (app, owner, n_tasks,
    n_task_runs, overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, "Delete")
    require.app.read(app)
    require.app.delete(app)
    if request.method == 'GET':
        return render_template('/applications/delete.html',
                               title=title,
                               app=app,
                               owner=owner,
                               n_tasks=n_tasks,
                               overall_progress=overall_progress,
                               last_activity=last_activity)
    # Clean cache
    cached_apps.delete_app(app.short_name)
    cached_apps.clean(app.id)
    app = App.query.get(app.id)
    db.session.delete(app)
    db.session.commit()
    flash(gettext('Project deleted!'), 'success')
    return redirect(url_for('account.profile', name=current_user.name))


@blueprint.route('/<short_name>/update', methods=['GET', 'POST'])
@login_required
def update(short_name):
    (app, owner, n_tasks,
     n_task_runs, overall_progress, last_activity) = app_by_shortname(short_name)

    def handle_valid_form(form):
        hidden = int(form.hidden.data)

        (app, owner, n_tasks, n_task_runs,
         overall_progress, last_activity) = app_by_shortname(short_name)

        new_application = model.app.App(
            id=form.id.data,
            name=form.name.data,
            short_name=form.short_name.data,
            description=form.description.data,
            long_description=form.long_description.data,
            hidden=hidden,
            info=app.info,
            owner_id=app.owner_id,
            allow_anonymous_contributors=form.allow_anonymous_contributors.data,
            category_id=form.category_id.data)

        new_application.set_password(form.password.data)
        db.session.merge(new_application)
        db.session.commit()
        cached_apps.delete_app(short_name)
        cached_apps.reset()
        cached_cat.reset()
        cached_apps.get_app(new_application.short_name)
        flash(gettext('Project updated!'), 'success')
        return redirect(url_for('.details',
                                short_name=new_application.short_name))

    require.app.read(app)
    require.app.update(app)

    title = app_title(app, "Update")
    if request.method == 'GET':
        form = AppUpdateForm(obj=app)
        upload_form = AvatarUploadForm()
        categories = db.session.query(model.category.Category).all()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        if app.category_id is None:
            app.category_id = categories[0].id
        form.populate_obj(app)

    if request.method == 'POST':
        upload_form = AvatarUploadForm()
        form = AppUpdateForm(request.form)
        categories = cached_cat.get_all()
        form.category_id.choices = [(c.id, c.name) for c in categories]

        if request.form.get('btn') != 'Upload':
            if form.validate():
                return handle_valid_form(form)
            flash(gettext('Please correct the errors'), 'error')
        else:
            if upload_form.validate_on_submit():
                app = App.query.get(app.id)
                file = request.files['avatar']
                coordinates = (upload_form.x1.data, upload_form.y1.data,
                               upload_form.x2.data, upload_form.y2.data)
                prefix = time.time()
                file.filename = "app_%s_thumbnail_%i.png" % (app.id, prefix)
                container = "user_%s" % current_user.id
                uploader.upload_file(file,
                                     container=container,
                                     coordinates=coordinates)
                # Delete previous avatar from storage
                if app.info.get('thumbnail'):
                    uploader.delete_file(app.info['thumbnail'], container)
                app.info['thumbnail'] = file.filename
                app.info['container'] = container
                db.session.commit()
                cached_apps.delete_app(app.short_name)
                flash(gettext('Your project thumbnail has been updated! It may \
                                  take some minutes to refresh...'), 'success')
            else:
                flash(gettext('You must provide a file to change the avatar'),
                      'error')
            return redirect(url_for('.update', short_name=short_name))

    app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    return render_template('/applications/update.html',
                           form=form,
                           upload_form=upload_form,
                           app=app,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           n_task_runs=n_task_runs,
                           last_activity=last_activity,
                           n_completed_tasks=cached_apps.n_completed_tasks(app.get('id')),
                           n_volunteers=cached_apps.n_volunteers(app.get('id')),
                           title=title)


@blueprint.route('/<short_name>/')
def details(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)

    require.app.read(app)
    template = '/applications/app.html'

    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password

    title = app_title(app, None)
    app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    template_args = {"app": app, "title": title,
                     "owner": owner,
                     "n_tasks": n_tasks,
                     "overall_progress": overall_progress,
                     "last_activity": last_activity,
                     "n_completed_tasks": cached_apps.n_completed_tasks(app.get('id')),
                     "n_volunteers": cached_apps.n_volunteers(app.get('id'))}
    if current_app.config.get('CKAN_URL'):
        template_args['ckan_name'] = current_app.config.get('CKAN_NAME')
        template_args['ckan_url'] = current_app.config.get('CKAN_URL')
        template_args['ckan_pkg_name'] = short_name
    return render_template(template, **template_args)


@blueprint.route('/<short_name>/settings')
@login_required
def settings(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)

    title = app_title(app, "Settings")
    require.app.read(app)
    require.app.update(app)
    app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    return render_template('/applications/settings.html',
                           app=app,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           n_task_runs=n_task_runs,
                           last_activity=last_activity,
                           n_completed_tasks=cached_apps.n_completed_tasks(app.get('id')),
                           n_volunteers=cached_apps.n_volunteers(app.get('id')),
                           title=title)


def compute_importer_variant_pairs(forms):
    """Return a list of pairs of importer variants. The pair-wise enumeration
    is due to UI design.
    """
    # variants = reduce(operator.__add__,
    #                   [i.variants for i in forms.itervalues()],
    #                   [])
    # if len(variants) % 2: # pragma: no cover
    #     variants.append("empty")
    variants = ('epicollect', 'csv', 'gdocs-map', 'gdocs-sound', 'gdocs-spreadsheet', 'gdocs-image', 'gdocs-pdf', 'gdocs-video')
    prefix = "applications/tasks/"

    importer_variants = map(lambda i: "%s%s.html" % (prefix, i), variants)
    return [
        (importer_variants[i * 2], importer_variants[i * 2 + 1])
        for i in xrange(0, int(math.ceil(len(variants) / 2.0)))]



@blueprint.route('/<short_name>/tasks/import', methods=['GET', 'POST'])
@login_required
def import_task(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    n_volunteers = cached_apps.n_volunteers(app.id)
    n_completed_tasks = cached_apps.n_completed_tasks(app.id)
    title = app_title(app, "Import Tasks")
    loading_text = gettext("Importing tasks, this may take a while, wait...")
    dict_app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    template_args = dict(title=title, loading_text=loading_text,
                         app=dict_app,
                         owner=owner,
                         n_tasks=n_tasks,
                         overall_progress=overall_progress,
                         n_volunteers=n_volunteers,
                         n_completed_tasks=n_completed_tasks)
    require.app.read(app)
    require.app.update(app)

    def render_forms():
        tmpl = '/applications/importers/%s.html' % template
        return render_template(tmpl, **template_args)

    forms = { 'csv': BulkTaskCSVImportForm,
              'gdocs': BulkTaskGDImportForm,
              'epicollect': BulkTaskEpiCollectPlusImportForm }
    template_args["importer_variants"] = compute_importer_variant_pairs(importer.importers)
    template = request.args.get('template')

    if not (template or request.method == 'POST'):
        return render_template('/applications/import_options.html',
                               **template_args)

    template = template if request.method == 'GET' else request.form['form_name']
    form = forms[template](request.form)
    template_args['form'] = form
    if template == 'gdocs':  # pragma: no cover
        mode = request.args.get('mode')
        if mode is not None:
            template_args["form"].googledocs_url.data = importer.googledocs_urls[mode]

    if not (form and form.validate_on_submit()):  # pragma: no cover
        return render_forms()

    handler = importer.importers[template]()
    _import_task(app, handler, form)
    return render_forms()


def _import_task(app, handler, form):
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


@blueprint.route('/<short_name>/password', methods=['GET', 'POST'])
def password_required(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    form = PasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        password = request.form.get('password')
        cookie_exp = current_app.config.get('PASSWD_COOKIE_TIMEOUT')
        passwd_mngr = ProjectPasswdManager(CookieHandler(request, signer, cookie_exp))
        if passwd_mngr.validates(password, app):
            response = make_response(redirect(request.args.get('next')))
            return passwd_mngr.update_response(response, app, get_user_id_or_ip())
        flash('Sorry, incorrect password')
    return render_template('applications/password.html',
                            app=app,
                            form=form,
                            short_name=short_name,
                            next=request.args.get('next'))


@blueprint.route('/<short_name>/task/<int:task_id>')
def task_presenter(short_name, task_id):
    (app, owner,
     n_tasks, n_task_runs, overall_progress, last_activity) = app_by_shortname(short_name)
    task = Task.query.filter_by(id=task_id).first_or_404()

    require.app.read(app)
    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password

    if current_user.is_anonymous():
        if not app.allow_anonymous_contributors:
            msg = ("Oops! You have to sign in to participate in "
                   "<strong>%s</strong>"
                   "project" % app.name)
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
    template_args = {"app": app, "title": title, "owner": owner}

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

    def invite_new_volunteers():
        user_id = None if current_user.is_anonymous() else current_user.id
        user_ip = request.remote_addr if current_user.is_anonymous() else None
        task = sched.new_task(app.id, user_id, user_ip, 0)
        return task is None and overall_progress < 100.0

    def respond(tmpl):
        if (current_user.is_anonymous()):
            msg_1 = gettext(msg)
            flash(msg_1, "warning")
        resp = make_response(render_template(tmpl, **template_args))
        return resp

    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, "Contribute")
    template_args = {"app": app, "title": title, "owner": owner,
                     "invite_new_volunteers": invite_new_volunteers()}
    require.app.read(app)
    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password

    if not app.allow_anonymous_contributors and current_user.is_anonymous():
        msg = "Oops! You have to sign in to participate in <strong>%s</strong> \
               project" % app.name
        flash(gettext(msg), 'warning')
        return redirect(url_for('account.signin',
                        next=url_for('.presenter', short_name=app.short_name)))

    msg = "Ooops! You are an anonymous user and will not \
           get any credit for your contributions. Sign in \
           now!"

    if app.info.get("tutorial") and \
            request.cookies.get(app.short_name + "tutorial") is None:
        resp = respond('/applications/tutorial.html')
        resp.set_cookie(app.short_name + 'tutorial', 'seen')
        return resp
    else:
        return respond('/applications/presenter.html')


@blueprint.route('/<short_name>/tutorial')
def tutorial(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, "Tutorial")

    require.app.read(app)
    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password
    return render_template('/applications/tutorial.html', title=title,
                           app=app, owner=owner)


@blueprint.route('/<short_name>/<int:task_id>/results.json')
def export(short_name, task_id):
    """Return a file with all the TaskRuns for a give Task"""
    try:
        session = get_session(db, bind='slave')
        # Check if the app exists
        (app, owner, n_tasks, n_task_runs,
         overall_progress, last_activity) = app_by_shortname(short_name)

        require.app.read(app)
        redirect_to_password = _check_if_redirect_to_password(app)
        if redirect_to_password:
            return redirect_to_password

        # Check if the task belongs to the app and exists
        task = session.query(model.task.Task).filter_by(app_id=app.id)\
                                             .filter_by(id=task_id).first()
        if task:
            taskruns = session.query(model.task_run.TaskRun).filter_by(task_id=task_id)\
                              .filter_by(app_id=app.id).all()
            results = [tr.dictize() for tr in taskruns]
            return Response(json.dumps(results), mimetype='application/json')
        else:
            return abort(404)
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@blueprint.route('/<short_name>/tasks/')
def tasks(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, "Tasks")

    require.app.read(app)
    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password
    app = add_custom_contrib_button_to(app, get_user_id_or_ip())

    return render_template('/applications/tasks.html',
                           title=title,
                           app=app,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           last_activity=last_activity,
                           n_completed_tasks=cached_apps.n_completed_tasks(app.get('id')),
                           n_volunteers=cached_apps.n_volunteers(app.get('id')))


@blueprint.route('/<short_name>/tasks/browse', defaults={'page': 1})
@blueprint.route('/<short_name>/tasks/browse/<int:page>')
def tasks_browse(short_name, page):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, "Tasks")
    n_volunteers = cached_apps.n_volunteers(app.id)
    n_completed_tasks = cached_apps.n_completed_tasks(app.id)

    def respond():
        try:
            session = get_session(db, bind='slave')
            per_page = 10
            count = session.query(model.task.Task)\
                .filter_by(app_id=app.get('id'))\
                .count()
            app_tasks = session.query(model.task.Task)\
                .filter_by(app_id=app.get('id'))\
                .order_by(model.task.Task.id)\
                .limit(per_page)\
                .offset((page - 1) * per_page)\
                .all()

            if not app_tasks and page != 1:
                abort(404)

            pagination = Pagination(page, per_page, count)
            return render_template('/applications/tasks_browse.html',
                                   app=app,
                                   owner=owner,
                                   tasks=app_tasks,
                                   title=title,
                                   pagination=pagination,
                                   n_tasks=n_tasks,
                                   overall_progress=overall_progress,
                                   n_volunteers=n_volunteers,
                                   n_completed_tasks=n_completed_tasks)
        except: # pragma: no cover
            session.rollback()
            raise
        finally:
            session.close()

    require.app.read(app)
    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password
    app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    return respond()


@blueprint.route('/<short_name>/tasks/delete', methods=['GET', 'POST'])
@login_required
def delete_tasks(short_name):
    """Delete ALL the tasks for a given project"""
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    require.app.read(app)
    require.app.update(app)
    if request.method == 'GET':
        title = app_title(app, "Delete")
        n_volunteers = cached_apps.n_volunteers(app.id)
        n_completed_tasks = cached_apps.n_completed_tasks(app.id)
        app = add_custom_contrib_button_to(app, get_user_id_or_ip())
        return render_template('applications/tasks/delete.html',
                               app=app,
                               owner=owner,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks,
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


@blueprint.route('/<short_name>/tasks/export')
def export_to(short_name):
    """Export Tasks and TaskRuns in the given format"""
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    n_volunteers = cached_apps.n_volunteers(app.id)
    n_completed_tasks = cached_apps.n_completed_tasks(app.id)
    title = app_title(app, gettext("Export"))
    loading_text = gettext("Exporting data..., this may take a while")

    require.app.read(app)
    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password

    def respond():
        return render_template('/applications/export.html',
                               title=title,
                               loading_text=loading_text,
                               ckan_name=current_app.config.get('CKAN_NAME'),
                               app=app,
                               owner=owner,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks,
                               overall_progress=overall_progress)


    def gen_json(table):
        try:
            session = get_session(db, bind='slave')
            n = session.query(table)\
                .filter_by(app_id=app.id).count()
            sep = ", "
            yield "["
            for i, tr in enumerate(session.query(table)
                                     .filter_by(app_id=app.id).yield_per(1), 1):
                item = json.dumps(tr.dictize())
                if (i == n):
                    sep = ""
                yield item + sep
            yield "]"
        except: # pragma: no cover
            session.rollback()
            raise
        finally:
            session.close()

    def format_csv_properly(row, ty=None):
        tmp = row.keys()
        task_keys = []
        for k in tmp:
            k = "%s__%s" % (ty, k)
            task_keys.append(k)
        if (type(row['info']) == dict):
            task_info_keys = []
            tmp = row['info'].keys()
            for k in tmp:
                k = "%sinfo__%s" % (ty, k)
                task_info_keys.append(k)
        else:
            task_info_keys = []

        keys = sorted(task_keys + task_info_keys)
        values = []
        _prefix = "%sinfo" % ty
        for k in keys:
            prefix, k = k.split("__")
            if prefix == _prefix:
                if row['info'].get(k) is not None:
                    values.append(row['info'][k])
                else:
                    values.append(None)
            else:
                if row.get(k) is not None:
                    values.append(row[k])
                else:
                    values.append(None)

        return values

    def handle_task(writer, t):
        writer.writerow(format_csv_properly(t.dictize(), ty='task'))

    def handle_task_run(writer, t):
        writer.writerow(format_csv_properly(t.dictize(), ty='taskrun'))

    def get_csv(out, writer, table, handle_row):
        try:
            session = get_session(db, bind='slave')
            for tr in session.query(table)\
                    .filter_by(app_id=app.id)\
                    .yield_per(1):
                handle_row(writer, tr)
            yield out.getvalue()
        except: # pragma: no cover
            session.rollback()
            raise
        finally:
            session.close()

    def respond_json(ty):
        tables = {"task": model.task.Task, "task_run": model.task_run.TaskRun}
        try:
            table = tables[ty]
        except KeyError:
            return abort(404)

        tmp = 'attachment; filename=%s_%s.json' % (app.short_name, ty)
        res = Response(gen_json(table), mimetype='application/json')
        res.headers['Content-Disposition'] = tmp
        return res

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
        try:
            session = get_session(db, bind='slave')
            # Export Task(/Runs) to CSV
            types = {
                "task": (
                    model.task.Task, handle_task,
                    (lambda x: True),
                    gettext(
                        "Oops, the project does not have tasks to \
                        export, if you are the owner add some tasks")),
                "task_run": (
                    model.task_run.TaskRun, handle_task_run,
                    (lambda x: True),
                    gettext(
                        "Oops, there are no Task Runs yet to export, invite \
                         some users to participate"))}
            try:
                table, handle_row, test, msg = types[ty]
            except KeyError:
                return abort(404)

            out = StringIO()
            writer = UnicodeWriter(out)
            t = session.query(table)\
                .filter_by(app_id=app.id)\
                .first()
            if t is not None:
                if test(t):
                    tmp = t.dictize().keys()
                    task_keys = []
                    for k in tmp:
                        k = "%s__%s" % (ty, k)
                        task_keys.append(k)
                    if (type(t.info) == dict):
                        task_info_keys = []
                        tmp = t.info.keys()
                        for k in tmp:
                            k = "%sinfo__%s" % (ty, k)
                            task_info_keys.append(k)
                    else:
                        task_info_keys = []
                    keys = task_keys + task_info_keys
                    writer.writerow(sorted(keys))

                res = Response(get_csv(out, writer, table, handle_row),
                               mimetype='text/csv')
                tmp = 'attachment; filename=%s_%s.csv' % (app.short_name, ty)
                res.headers['Content-Disposition'] = tmp
                return res
            else:
                flash(msg, 'info')
                return respond()
        except: # pragma: no cover
            session.rollback()
            raise
        finally:
            session.close()

    export_formats = ["json", "csv"]
    if current_user.is_authenticated():
        if current_user.ckan_api:
            export_formats.append('ckan')

    ty = request.args.get('type')
    fmt = request.args.get('format')
    if not (fmt and ty):
        if len(request.args) >= 1:
            abort(404)
        app = add_custom_contrib_button_to(app, get_user_id_or_ip())
        return render_template('/applications/export.html',
                               title=title,
                               loading_text=loading_text,
                               ckan_name=current_app.config.get('CKAN_NAME'),
                               app=app,
                               owner=owner,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks,
                               overall_progress=overall_progress)
    if fmt not in export_formats:
        abort(415)
    return {"json": respond_json, "csv": respond_csv, 'ckan': respond_ckan}[fmt](ty)


@blueprint.route('/<short_name>/stats')
def show_stats(short_name):
    """Returns App Stats"""
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    n_volunteers = cached_apps.n_volunteers(app.id)
    n_completed_tasks = cached_apps.n_completed_tasks(app.id)
    title = app_title(app, "Statistics")

    require.app.read(app)
    redirect_to_password = _check_if_redirect_to_password(app)
    if redirect_to_password:
        return redirect_to_password

    if not ((n_tasks > 0) and (n_task_runs > 0)):
        app = add_custom_contrib_button_to(app, get_user_id_or_ip())
        return render_template('/applications/non_stats.html',
                               title=title,
                               app=app,
                               owner=owner,
                               n_tasks=n_tasks,
                               overall_progress=overall_progress,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks)

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

    app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    return render_template('/applications/stats.html',
                           title=title,
                           appStats=json.dumps(tmp),
                           userStats=userStats,
                           app=app,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           n_volunteers=n_volunteers,
                           n_completed_tasks=n_completed_tasks)


@blueprint.route('/<short_name>/tasks/settings')
@login_required
def task_settings(short_name):
    """Settings page for tasks of the project"""
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    n_volunteers = cached_apps.n_volunteers(app.id)
    n_completed_tasks = cached_apps.n_completed_tasks(app.id)
    require.app.read(app)
    require.app.update(app)
    app = add_custom_contrib_button_to(app, get_user_id_or_ip())
    return render_template('applications/task_settings.html',
                           app=app,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           n_volunteers=n_volunteers,
                           n_completed_tasks=n_completed_tasks)


@blueprint.route('/<short_name>/tasks/redundancy', methods=['GET', 'POST'])
@login_required
def task_n_answers(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, gettext('Redundancy'))
    form = TaskRedundancyForm()
    require.app.read(app)
    require.app.update(app)
    if request.method == 'GET':
        return render_template('/applications/task_n_answers.html',
                               title=title,
                               form=form,
                               app=app,
                               owner=owner)
    elif request.method == 'POST' and form.validate():
        sql = text('''
                   UPDATE task SET n_answers=:n_answers,
                   state='ongoing' WHERE app_id=:app_id''').execution_options(autocommit=True)

        db.session.execute(sql, dict(n_answers=form.n_answers.data, app_id=app.id))

        # Update task.state according to their new n_answers value
        sql = text('''
                   WITH myquery AS (
                   SELECT task.id, task.n_answers,
                   COUNT(task_run.id) AS n_task_runs, task.state
                   FROM task, task_run
                   WHERE task_run.task_id=task.id AND task.app_id=:app_id
                   GROUP BY task.id)
                   UPDATE task SET state='completed'
                   FROM myquery
                   WHERE (myquery.n_task_runs >=:n_answers)
                   and myquery.id=task.id
                   ''').execution_options(autocommit=True)

        db.session.execute(sql, dict(n_answers=form.n_answers.data, app_id=app.id))

        msg = gettext('Redundancy of Tasks updated!')
        flash(msg, 'success')
        return redirect(url_for('.tasks', short_name=app.short_name))
    else:
        flash(gettext('Please correct the errors'), 'error')
        return render_template('/applications/task_n_answers.html',
                               title=title,
                               form=form,
                               app=app,
                               owner=owner)


@blueprint.route('/<short_name>/tasks/scheduler', methods=['GET', 'POST'])
@login_required
def task_scheduler(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, gettext('Task Scheduler'))
    form = TaskSchedulerForm()

    def respond():
        return render_template('/applications/task_scheduler.html',
                               title=title,
                               form=form,
                               app=app,
                               owner=owner)
    require.app.read(app)
    require.app.update(app)

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
        msg = gettext("Project Task Scheduler updated!")
        flash(msg, 'success')
        return redirect(url_for('.tasks', short_name=app.short_name))
    else: # pragma: no cover
        flash(gettext('Please correct the errors'), 'error')
        return respond()


@blueprint.route('/<short_name>/tasks/priority', methods=['GET', 'POST'])
@login_required
def task_priority(short_name):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)
    title = app_title(app, gettext('Task Priority'))
    form = TaskPriorityForm()

    def respond():
        return render_template('/applications/task_priority.html',
                               title=title,
                               form=form,
                               app=app,
                               owner=owner)
    require.app.read(app)
    require.app.update(app)

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
    try:
        session = get_session(db, bind='slave')
        (app, owner, n_tasks, n_task_runs,
         overall_progress, last_activity) = app_by_shortname(short_name)

        blogposts = session.query(model.blogpost.Blogpost).filter_by(app_id=app.id).all()
        require.blogpost.read(app_id=app.id)
        redirect_to_password = _check_if_redirect_to_password(app)
        if redirect_to_password:
            return redirect_to_password
        app = add_custom_contrib_button_to(app, get_user_id_or_ip())
        return render_template('applications/blog.html', app=app,
                               owner=owner, blogposts=blogposts,
                               overall_progress=overall_progress,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_completed_tasks=cached_apps.n_completed_tasks(app.get('id')),
                               n_volunteers=cached_apps.n_volunteers(app.get('id')))
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@blueprint.route('/<short_name>/<int:id>')
def show_blogpost(short_name, id):
    try:
        session = get_session(db, bind='slave')
        (app, owner, n_tasks, n_task_runs,
         overall_progress, last_activity) = app_by_shortname(short_name)
        blogpost = session.query(model.blogpost.Blogpost).filter_by(id=id,
                                                            app_id=app.id).first()
        if blogpost is None:
            raise abort(404)
        require.blogpost.read(blogpost)
        redirect_to_password = _check_if_redirect_to_password(app)
        if redirect_to_password:
            return redirect_to_password
        app = add_custom_contrib_button_to(app, get_user_id_or_ip())
        return render_template('applications/blog_post.html',
                                app=app,
                                owner=owner,
                                blogpost=blogpost,
                                overall_progress=overall_progress,
                                n_tasks=n_tasks,
                                n_task_runs=n_task_runs,
                                n_completed_tasks=cached_apps.n_completed_tasks(app.get('id')),
                                n_volunteers=cached_apps.n_volunteers(app.get('id')))
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@blueprint.route('/<short_name>/new-blogpost', methods=['GET', 'POST'])
@login_required
def new_blogpost(short_name):

    def respond():
        dict_app = add_custom_contrib_button_to(app, get_user_id_or_ip())
        return render_template('applications/new_blogpost.html',
                               title=gettext("Write a new post"),
                               form=form,
                               app=dict_app,
                               owner=owner,
                               overall_progress=overall_progress,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_completed_tasks=cached_apps.n_completed_tasks(dict_app.get('id')),
                               n_volunteers=cached_apps.n_volunteers(dict_app.get('id')))


    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)

    form = BlogpostForm(request.form)
    del form.id

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


@blueprint.route('/<short_name>/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update_blogpost(short_name, id):
    (app, owner, n_tasks, n_task_runs,
     overall_progress, last_activity) = app_by_shortname(short_name)

    blogpost = db.session.query(model.blogpost.Blogpost).filter_by(id=id,
                                                        app_id=app.id).first()
    if blogpost is None:
        raise abort(404)

    def respond():
        return render_template('applications/update_blogpost.html',
                               title=gettext("Edit a post"),
                               form=form, app=app, owner=owner,
                               blogpost=blogpost,
                               overall_progress=overall_progress,
                               n_task_runs=n_task_runs,
                               n_completed_tasks=cached_apps.n_completed_tasks(app.id),
                               n_volunteers=cached_apps.n_volunteers(app.id))

    form = BlogpostForm()

    if request.method != 'POST':
        require.blogpost.update(blogpost)
        form = BlogpostForm(obj=blogpost)
        return respond()

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond()

    require.blogpost.update(blogpost)
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


@blueprint.route('/<short_name>/<int:id>/delete', methods=['POST'])
@login_required
def delete_blogpost(short_name, id):
    app = app_by_shortname(short_name)[0]
    blogpost = db.session.query(model.blogpost.Blogpost).filter_by(id=id,
                                                        app_id=app.id).first()
    if blogpost is None:
        raise abort(404)

    require.blogpost.delete(blogpost)
    db.session.delete(blogpost)
    db.session.commit()
    cached_apps.delete_app(short_name)
    flash('<i class="icon-ok"></i> ' + 'Blog post deleted!', 'success')
    return redirect(url_for('.show_blogposts', short_name=short_name))



def _check_if_redirect_to_password(app):
    cookie_exp = current_app.config.get('PASSWD_COOKIE_TIMEOUT')
    passwd_mngr = ProjectPasswdManager(CookieHandler(request, signer, cookie_exp))
    if passwd_mngr.password_needed(app, get_user_id_or_ip()):
        return redirect(url_for('.password_required',
                                 short_name=app.short_name, next=request.path))

