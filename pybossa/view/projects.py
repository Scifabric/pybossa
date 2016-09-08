# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, ort
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
import os
import math
import requests
from StringIO import StringIO

from flask import Blueprint, request, url_for, flash, redirect, abort, Response, current_app
from flask import render_template, make_response, session
from flask.ext.login import login_required, current_user
from flask.ext.babel import gettext
from rq import Queue

import pybossa.sched as sched

from pybossa.core import (uploader, signer, sentinel, json_exporter,
    csv_exporter, importer, sentinel)
from pybossa.model.project import Project
from pybossa.model.category import Category
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.auditlog import Auditlog
from pybossa.model.webhook import Webhook
from pybossa.model.blogpost import Blogpost
from pybossa.util import Pagination, admin_required, get_user_id_or_ip, rank
from pybossa.auth import ensure_authorized_to
from pybossa.cache import projects as cached_projects
from pybossa.cache import categories as cached_cat
from pybossa.cache import project_stats as stats
from pybossa.cache.helpers import add_custom_contrib_button_to, has_no_presenter
from pybossa.ckan import Ckan
from pybossa.extensions import misaka
from pybossa.cookies import CookieHandler
from pybossa.password_manager import ProjectPasswdManager
from pybossa.jobs import import_tasks, IMPORT_TASKS_TIMEOUT, webhook
from pybossa.forms.projects_view_forms import *
from pybossa.importers import BulkImportException
from pybossa.pro_features import ProFeatureHandler

from pybossa.core import project_repo, user_repo, task_repo, blog_repo
from pybossa.core import webhook_repo, auditlog_repo
from pybossa.auditlogger import AuditLogger
from pybossa.contributions_guard import ContributionsGuard

blueprint = Blueprint('project', __name__)

MAX_NUM_SYNCHRONOUS_TASKS_IMPORT = 200
auditlogger = AuditLogger(auditlog_repo, caller='web')
importer_queue = Queue('medium',
                       connection=sentinel.master,
                       default_timeout=IMPORT_TASKS_TIMEOUT)
webhook_queue = Queue('high', connection=sentinel.master)

def project_title(project, page_name):
    if not project:  # pragma: no cover
        return "Project not found"
    if page_name is None:
        return "Project: %s" % (project.name)
    return "Project: %s &middot; %s" % (project.name, page_name)


def project_by_shortname(short_name):
    project = cached_projects.get_project(short_name)
    if project:
        # Get owner
        owner = user_repo.get(project.owner_id)
        # Populate CACHE with the data of the project
        return (project,
                owner,
                cached_projects.n_tasks(project.id),
                cached_projects.n_task_runs(project.id),
                cached_projects.overall_progress(project.id),
                cached_projects.last_activity(project.id),
                cached_projects.n_results(project.id))
    else:
        cached_projects.delete_project(short_name)
        return abort(404)


def pro_features(owner=None):
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    pro = {
        'auditlog_enabled': feature_handler.auditlog_enabled_for(current_user),
        'autoimporter_enabled': feature_handler.autoimporter_enabled_for(current_user),
        'webhooks_enabled': feature_handler.webhooks_enabled_for(current_user)
    }
    if owner:
        pro['better_stats_enabled'] = feature_handler.better_stats_enabled_for(
                                          current_user,
                                          owner)
    return pro


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>/', defaults={'page': 1})
@login_required
@admin_required
def redirect_old_featured(page):
    """DEPRECATED only to redirect old links"""
    return redirect(url_for('.index', page=page), 301)


@blueprint.route('/published/', defaults={'page': 1})
@blueprint.route('/published/<int:page>/', defaults={'page': 1})
@login_required
@admin_required
def redirect_old_published(page):  # pragma: no cover
    """DEPRECATED only to redirect old links"""
    category = project_repo.get_category()
    return redirect(url_for('.project_cat_index', category=category.short_name, page=page), 301)


@blueprint.route('/draft/', defaults={'page': 1})
@blueprint.route('/draft/<int:page>/', defaults={'page': 1})
@login_required
@admin_required
def redirect_old_draft(page):
    """DEPRECATED only to redirect old links"""
    return redirect(url_for('.draft', page=page), 301)


@blueprint.route('/category/featured/', defaults={'page': 1})
@blueprint.route('/category/featured/page/<int:page>/')
@login_required
@admin_required
def index(page):
    """List projects in the system"""
    if cached_projects.n_count('featured') > 0:
        return project_index(page, cached_projects.get_all_featured, 'featured',
                         True, False)
    else:
        categories = cached_cat.get_all()
        cat_short_name = categories[0].short_name
        return redirect(url_for('.project_cat_index', category=cat_short_name))


def project_index(page, lookup, category, fallback, use_count):
    """Show projects of a category"""

    per_page = current_app.config['APPS_PER_PAGE']

    ranked_projects = rank(lookup(category))
    offset = (page - 1) * per_page
    projects = ranked_projects[offset:offset+per_page]

    count = cached_projects.n_count(category)

    data = []

    if fallback and not projects:  # pragma: no cover
        return redirect(url_for('.index'))

    pagination = Pagination(page, per_page, count)
    categories = cached_cat.get_all()
    # Check for pre-defined categories featured and draft
    featured_cat = Category(name='Featured',
                            short_name='featured',
                            description='Featured projects')
    if category == 'featured':
        active_cat = featured_cat
    elif category == 'draft':
        active_cat = Category(name='Draft',
                              short_name='draft',
                              description='Draft projects')
    else:
        active_cat = project_repo.get_category_by(short_name=category)

    # Check if we have to add the section Featured to local nav
    if cached_projects.n_count('featured') > 0:
        categories.insert(0, featured_cat)
    template_args = {
        "projects": projects,
        "title": gettext("Projects"),
        "pagination": pagination,
        "active_cat": active_cat,
        "categories": categories}

    if use_count:
        template_args.update({"count": count})
    return render_template('/projects/index.html', **template_args)


@blueprint.route('/category/draft/', defaults={'page': 1})
@blueprint.route('/category/draft/page/<int:page>/')
@login_required
@admin_required
def draft(page):
    """Show the Draft projects"""
    return project_index(page, cached_projects.get_all_draft, 'draft',
                     False, True)


@blueprint.route('/category/<string:category>/', defaults={'page': 1})
@blueprint.route('/category/<string:category>/page/<int:page>/')
@login_required
@admin_required
def project_cat_index(category, page):
    """Show Projects that belong to a given category"""
    return project_index(page, cached_projects.get_all, category, False, True)


@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new():
    ensure_authorized_to('create', Project)
    form = ProjectForm(request.form)

    def respond(errors):
        return render_template('projects/new.html',
                               title=gettext("Create a Project"),
                               form=form, errors=errors)

    def _description_from_long_description():
        if form.description.data:
            return form.description.data
        long_desc = form.long_description.data
        html_long_desc = misaka.render(long_desc)[:-1]
        remove_html_tags_regex = re.compile('<[^>]*>')
        blank_space_regex = re.compile('\n')
        text_desc = remove_html_tags_regex.sub("", html_long_desc)[:255]
        if len(text_desc) >= 252:
            text_desc = text_desc[:-3]
            text_desc += "..."
        description = blank_space_regex.sub(" ", text_desc)
        return description if description else " "

    if request.method != 'POST':
        return respond(False)

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond(True)

    info = {}
    category_by_default = cached_cat.get_all()[0]

    project = Project(name=form.name.data,
              short_name=form.short_name.data,
              description=_description_from_long_description(),
              long_description=form.long_description.data,
              owner_id=current_user.id,
              info=info,
              category_id=category_by_default.id)

    project_repo.save(project)

    msg_1 = gettext('Project created!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')
    flash('<i class="icon-bullhorn"></i> ' +
          gettext('You can check the ') +
          '<strong><a href="https://docs.pybossa.com">' +
          gettext('Guide and Documentation') +
          '</a></strong> ' +
          gettext('for adding tasks, a thumbnail, using PyBossa.JS, etc.'),
          'info')
    auditlogger.add_log_entry(None, project, current_user)

    return redirect(url_for('.update', short_name=project.short_name))


@blueprint.route('/<short_name>/tasks/taskpresentereditor', methods=['GET', 'POST'])
@login_required
@admin_required
def task_presenter_editor(short_name):
    errors = False
    (project, owner, n_tasks, n_task_runs,
     overall_progress,
     last_activity, n_results) = project_by_shortname(short_name)

    title = project_title(project, "Task Presenter Editor")
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)

    pro = pro_features()

    form = TaskPresenterForm(request.form)
    form.id.data = project.id
    if request.method == 'POST' and form.validate():
        db_project = project_repo.get(project.id)
        old_project = Project(**db_project.dictize())
        old_info = dict(db_project.info)
        old_info['task_presenter'] = form.editor.data
        db_project.info = old_info
        auditlogger.add_log_entry(old_project, db_project, current_user)
        project_repo.update(db_project)
        msg_1 = gettext('Task presenter added!')
        flash('<i class="icon-ok"></i> ' + msg_1, 'success')
        return redirect(url_for('.tasks', short_name=project.short_name))

    # It does not have a validation
    if request.method == 'POST' and not form.validate():  # pragma: no cover
        flash(gettext('Please correct the errors'), 'error')
        errors = True

    if project.info.get('task_presenter'):
        form.editor.data = project.info['task_presenter']
    else:
        if not request.args.get('template'):
            msg_1 = gettext('<strong>Note</strong> You will need to upload the'
                            ' tasks using the')
            msg_2 = gettext('CSV importer')
            msg_3 = gettext(' or download the project bundle and run the'
                            ' <strong>createTasks.py</strong> script in your'
                            ' computer')
            url = '<a href="%s"> %s</a>' % (url_for('project.import_task',
                                                    short_name=project.short_name), msg_2)
            msg = msg_1 + url + msg_3
            flash(msg, 'info')

            wrap = lambda i: "projects/presenters/%s.html" % i
            pres_tmpls = map(wrap, current_app.config.get('PRESENTERS'))

            project = add_custom_contrib_button_to(project, get_user_id_or_ip())
            return render_template(
                'projects/task_presenter_options.html',
                title=title,
                project=project,
                owner=owner,
                overall_progress=overall_progress,
                n_tasks=n_tasks,
                n_task_runs=n_task_runs,
                last_activity=last_activity,
                n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                n_volunteers=cached_projects.n_volunteers(project.get('id')),
                presenters=pres_tmpls,
                pro_features=pro)

        tmpl_uri = "projects/snippets/%s.html" \
            % request.args.get('template')
        tmpl = render_template(tmpl_uri, project=project)
        form.editor.data = tmpl
        msg = 'Your code will be <em>automagically</em> rendered in \
                      the <strong>preview section</strong>. Click in the \
                      preview button!'
        flash(gettext(msg), 'info')
    dict_project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('projects/task_presenter_editor.html',
                           title=title,
                           form=form,
                           project=dict_project,
                           owner=owner,
                           overall_progress=overall_progress,
                           n_tasks=n_tasks,
                           n_task_runs=n_task_runs,
                           last_activity=last_activity,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.id),
                           n_volunteers=cached_projects.n_volunteers(project.id),
                           errors=errors,
                           pro_features=pro)


@blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete(short_name):
    (project, owner, n_tasks,
    n_task_runs, overall_progress, last_activity,
    n_results) = project_by_shortname(short_name)
    title = project_title(project, "Delete")
    ensure_authorized_to('read', project)
    ensure_authorized_to('delete', project)
    pro = pro_features()
    if request.method == 'GET':
        return render_template('/projects/delete.html',
                               title=title,
                               project=project,
                               owner=owner,
                               n_tasks=n_tasks,
                               overall_progress=overall_progress,
                               last_activity=last_activity,
                               pro_features=pro)
    project_repo.delete(project)
    auditlogger.add_log_entry(project, None, current_user)
    flash(gettext('Project deleted!'), 'success')
    return redirect(url_for('account.profile', name=current_user.name))


@blueprint.route('/<short_name>/update', methods=['GET', 'POST'])
@login_required
@admin_required
def update(short_name):
    (project, owner, n_tasks,
     n_task_runs, overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    def handle_valid_form(form):
        (project, owner, n_tasks, n_task_runs,
         overall_progress, last_activity,
         n_results) = project_by_shortname(short_name)

        new_project = project_repo.get_by_shortname(short_name)
        old_project = Project(**new_project.dictize())
        old_info = dict(new_project.info)
        old_project.info = old_info
        if form.id.data == new_project.id:
            new_project.name = form.name.data
            new_project.short_name = form.short_name.data
            new_project.description = form.description.data
            new_project.long_description = form.long_description.data
            new_project.webhook = form.webhook.data
            new_project.info = project.info
            new_project.owner_id = project.owner_id
            new_project.allow_anonymous_contributors = form.allow_anonymous_contributors.data
            new_project.category_id = form.category_id.data

        if form.protect.data and form.password.data:
            new_project.set_password(form.password.data)
        if not form.protect.data:
            new_project.set_password("")

        project_repo.update(new_project)
        auditlogger.add_log_entry(old_project, new_project, current_user)
        cached_cat.reset()
        cached_projects.get_project(new_project.short_name)
        flash(gettext('Project updated!'), 'success')
        return redirect(url_for('.details',
                                short_name=new_project.short_name))

    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)

    pro = pro_features()

    title = project_title(project, "Update")
    if request.method == 'GET':
        form = ProjectUpdateForm(obj=project)
        upload_form = AvatarUploadForm()
        categories = project_repo.get_all_categories()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        if project.category_id is None:
            project.category_id = categories[0].id
        form.populate_obj(project)
        form.protect.data = project.needs_password()

    if request.method == 'POST':
        upload_form = AvatarUploadForm()
        form = ProjectUpdateForm(request.form)
        categories = cached_cat.get_all()
        form.category_id.choices = [(c.id, c.name) for c in categories]

        if request.form.get('btn') != 'Upload':
            if form.validate():
                return handle_valid_form(form)
            flash(gettext('Please correct the errors'), 'error')
        else:
            if upload_form.validate_on_submit():
                project = project_repo.get(project.id)
                _file = request.files['avatar']
                coordinates = (upload_form.x1.data, upload_form.y1.data,
                               upload_form.x2.data, upload_form.y2.data)
                prefix = time.time()
                _file.filename = "project_%s_thumbnail_%i.png" % (project.id, prefix)
                container = "user_%s" % current_user.id
                uploader.upload_file(_file,
                                     container=container,
                                     coordinates=coordinates)
                # Delete previous avatar from storage
                if project.info.get('thumbnail'):
                    uploader.delete_file(project.info['thumbnail'], container)
                project.info['thumbnail'] = _file.filename
                project.info['container'] = container
                project_repo.save(project)
                flash(gettext('Your project thumbnail has been updated! It may \
                                  take some minutes to refresh...'), 'success')
            else:
                flash(gettext('You must provide a file to change the avatar'),
                      'error')
            return redirect(url_for('.update', short_name=short_name))

    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('/projects/update.html',
                           form=form,
                           upload_form=upload_form,
                           project=project,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           n_task_runs=n_task_runs,
                           last_activity=last_activity,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                           n_volunteers=cached_projects.n_volunteers(project.get('id')),
                           title=title,
                           pro_features=pro)


@blueprint.route('/<short_name>/')
@login_required
@admin_required
def details(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    template = '/projects/project.html'
    pro = pro_features()

    title = project_title(project, None)
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    template_args = {"project": project, "title": title,
                     "owner": owner,
                     "n_tasks": n_tasks,
                     "n_task_runs": n_task_runs,
                     "overall_progress": overall_progress,
                     "last_activity": last_activity,
                     "n_completed_tasks": cached_projects.n_completed_tasks(project.get('id')),
                     "n_volunteers": cached_projects.n_volunteers(project.get('id')),
                     "pro_features": pro}
    if current_app.config.get('CKAN_URL'):
        template_args['ckan_name'] = current_app.config.get('CKAN_NAME')
        template_args['ckan_url'] = current_app.config.get('CKAN_URL')
        template_args['ckan_pkg_name'] = short_name
    return render_template(template, **template_args)


@blueprint.route('/<short_name>/settings')
@login_required
@admin_required
def settings(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    title = project_title(project, "Settings")
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)
    pro = pro_features()
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('/projects/settings.html',
                           project=project,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           n_task_runs=n_task_runs,
                           last_activity=last_activity,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                           n_volunteers=cached_projects.n_volunteers(project.get('id')),
                           title=title,
                           pro_features=pro)


@blueprint.route('/<short_name>/tasks/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_task(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)

    n_volunteers = cached_projects.n_volunteers(project.id)
    n_completed_tasks = cached_projects.n_completed_tasks(project.id)
    title = project_title(project, "Import Tasks")
    loading_text = gettext("Importing tasks, this may take a while, wait...")
    pro = pro_features()
    dict_project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    template_args = dict(title=title, loading_text=loading_text,
                         project=dict_project,
                         owner=owner,
                         n_tasks=n_tasks,
                         overall_progress=overall_progress,
                         n_volunteers=n_volunteers,
                         n_completed_tasks=n_completed_tasks,
                         target='project.import_task',
                         pro_features=pro)

    importer_type = request.form.get('form_name') or request.args.get('type')
    all_importers = importer.get_all_importer_names()
    if importer_type is not None and importer_type not in all_importers:
        raise abort(404)
    form = GenericBulkTaskImportForm()(importer_type, request.form)
    template_args['form'] = form

    if request.method == 'POST':
        if form.validate():  # pragma: no cover
            try:
                return _import_tasks(project, **form.get_import_data())
            except BulkImportException as err_msg:
                flash(err_msg, 'error')
            except Exception as inst:  # pragma: no cover
                current_app.logger.error(inst)
                msg = 'Oops! Looks like there was an error!'
                flash(gettext(msg), 'error')
        return render_template('/projects/importers/%s.html' % importer_type,
                                **template_args)

    if request.method == 'GET':
        template_tasks = current_app.config.get('TEMPLATE_TASKS')
        if importer_type is None:
            template_wrap = lambda i: "projects/tasks/gdocs-%s.html" % i
            task_tmpls = map(template_wrap, template_tasks)
            template_args['task_tmpls'] = task_tmpls
            importer_wrap = lambda i: "projects/tasks/%s.html" % i
            template_args['available_importers'] = map(importer_wrap, all_importers)
            return render_template('/projects/task_import_options.html',
                                   **template_args)
        if importer_type == 'gdocs' and request.args.get('template'):  # pragma: no cover
            template = request.args.get('template')
            form.googledocs_url.data = template_tasks.get(template)
        return render_template('/projects/importers/%s.html' % importer_type,
                                **template_args)


def _import_tasks(project, **form_data):
    number_of_tasks = importer.count_tasks_to_import(**form_data)
    if number_of_tasks <= MAX_NUM_SYNCHRONOUS_TASKS_IMPORT:
        report = importer.create_tasks(task_repo, project.id, **form_data)
        flash(report.message)
    else:
        importer_queue.enqueue(import_tasks, project.id, **form_data)
        flash(gettext("You're trying to import a large amount of tasks, so please be patient.\
            You will receive an email when the tasks are ready."))
    return redirect(url_for('.tasks', short_name=project.short_name))


@blueprint.route('/<short_name>/tasks/autoimporter', methods=['GET', 'POST'])
@login_required
@admin_required
def setup_autoimporter(short_name):
    pro = pro_features()
    if not pro['autoimporter_enabled']:
        raise abort(403)

    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    n_volunteers = cached_projects.n_volunteers(project.id)
    n_completed_tasks = cached_projects.n_completed_tasks(project.id)
    dict_project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    template_args = dict(project=dict_project,
                         owner=owner,
                         n_tasks=n_tasks,
                         overall_progress=overall_progress,
                         n_volunteers=n_volunteers,
                         n_completed_tasks=n_completed_tasks,
                         pro_features=pro,
                         target='project.setup_autoimporter')
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)
    importer_type = request.form.get('form_name') or request.args.get('type')
    all_importers = importer.get_autoimporter_names()
    if importer_type is not None and importer_type not in all_importers:
        raise abort(404)
    form = GenericBulkTaskImportForm()(importer_type, request.form)
    template_args['form'] = form

    if project.has_autoimporter():
        current_autoimporter = project.get_autoimporter()
        importer_info = dict(**current_autoimporter)
        return render_template('/projects/task_autoimporter.html',
                                importer=importer_info, **template_args)

    if request.method == 'POST':
        if form.validate():  # pragma: no cover
            project.set_autoimporter(form.get_import_data())
            project_repo.save(project)
            auditlogger.log_event(project, current_user, 'create', 'autoimporter',
                                  'Nothing', json.dumps(project.get_autoimporter()))
            flash(gettext("Success! Tasks will be imported daily."))
            return redirect(url_for('.setup_autoimporter', short_name=project.short_name))

    if request.method == 'GET':
        if importer_type is None:
            wrap = lambda i: "projects/tasks/%s.html" % i
            template_args['available_importers'] = map(wrap, all_importers)
            return render_template('projects/task_autoimport_options.html',
                                   **template_args)
    return render_template('/projects/importers/%s.html' % importer_type,
                                **template_args)


@blueprint.route('/<short_name>/tasks/autoimporter/delete', methods=['POST'])
@login_required
@admin_required
def delete_autoimporter(short_name):
    pro = pro_features()
    if not pro['autoimporter_enabled']:
        raise abort(403)

    project = project_by_shortname(short_name)[0]

    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)
    if project.has_autoimporter():
        autoimporter = project.get_autoimporter()
        project.delete_autoimporter()
        project_repo.save(project)
        auditlogger.log_event(project, current_user, 'delete', 'autoimporter',
                              json.dumps(autoimporter), 'Nothing')
    return redirect(url_for('.tasks', short_name=project.short_name))


@blueprint.route('/<short_name>/password', methods=['GET', 'POST'])
def password_required(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    form = PasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        password = request.form.get('password')
        cookie_exp = current_app.config.get('PASSWD_COOKIE_TIMEOUT')
        passwd_mngr = ProjectPasswdManager(CookieHandler(request, signer, cookie_exp))
        if passwd_mngr.validates(password, project):
            response = make_response(redirect(request.args.get('next')))
            return passwd_mngr.update_response(response, project, get_user_id_or_ip())
        flash(gettext('Sorry, incorrect password'))
    return render_template('projects/password.html',
                            project=project,
                            form=form,
                            short_name=short_name,
                            next=request.args.get('next'))


@blueprint.route('/<short_name>/task/<int:task_id>')
def task_presenter(short_name, task_id):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    task = task_repo.get_task(id=task_id)
    if task is None:
        raise abort(404)
    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    if current_user.is_anonymous():
        if not project.allow_anonymous_contributors:
            msg = ("Oops! You have to sign in to participate in "
                   "<strong>%s</strong>"
                   "project" % project.name)
            flash(gettext(msg), 'warning')
            return redirect(url_for('account.signin',
                                    next=url_for('.presenter',
                                    short_name=project.short_name)))
        else:
            msg_1 = gettext(
                "Ooops! You are an anonymous user and will not "
                "get any credit"
                " for your contributions.")
            next_url = url_for('project.task_presenter',
                                short_name=short_name, task_id=task_id)
            url = url_for('account.signin', next=next_url)
            flash(msg_1 + "<a href=\"" + url + "\">Sign in now!</a>", "warning")

    title = project_title(project, "Contribute")
    template_args = {"project": project, "title": title, "owner": owner}

    def respond(tmpl):
        return render_template(tmpl, **template_args)

    if not (task.project_id == project.id):
        return respond('/projects/task/wrong.html')

    guard = ContributionsGuard(sentinel.master)
    guard.stamp(task, get_user_id_or_ip())

    if has_no_presenter(project):
        flash(gettext("Sorry, but this project is still a draft and does "
                      "not have a task presenter."), "error")
    return respond('/projects/presenter.html')


@blueprint.route('/<short_name>/presenter')
@blueprint.route('/<short_name>/newtask')
def presenter(short_name):

    def invite_new_volunteers(project):
        user_id = None if current_user.is_anonymous() else current_user.id
        user_ip = request.remote_addr if current_user.is_anonymous() else None
        task = sched.new_task(project.id, project.info.get('sched'), user_id, user_ip, 0)
        return task is None and overall_progress < 100.0

    def respond(tmpl):
        if (current_user.is_anonymous()):
            msg_1 = gettext(msg)
            flash(msg_1, "warning")
        resp = make_response(render_template(tmpl, **template_args))
        return resp

    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    title = project_title(project, "Contribute")
    template_args = {"project": project, "title": title, "owner": owner,
                     "invite_new_volunteers": invite_new_volunteers(project)}

    if not project.allow_anonymous_contributors and current_user.is_anonymous():
        msg = "Oops! You have to sign in to participate in <strong>%s</strong> \
               project" % project.name
        flash(gettext(msg), 'warning')
        return redirect(url_for('account.signin',
                        next=url_for('.presenter',
                                     short_name=project.short_name)))

    msg = "Ooops! You are an anonymous user and will not \
           get any credit for your contributions. Sign in \
           now!"

    if project.info.get("tutorial") and \
            request.cookies.get(project.short_name + "tutorial") is None:
        resp = respond('/projects/tutorial.html')
        resp.set_cookie(project.short_name + 'tutorial', 'seen')
        return resp
    else:
        if has_no_presenter(project):
            flash(gettext("Sorry, but this project is still a draft and does "
                          "not have a task presenter."), "error")
        return respond('/projects/presenter.html')


@blueprint.route('/<short_name>/tutorial')
def tutorial(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    title = project_title(project, "Tutorial")

    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    return render_template('/projects/tutorial.html', title=title,
                           project=project, owner=owner)


@blueprint.route('/<short_name>/<int:task_id>/results.json')
@login_required
@admin_required
def export(short_name, task_id):
    """Return a file with all the TaskRuns for a given Task"""
    # Check if the project exists
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    # Check if the task belongs to the project and exists
    task = task_repo.get_task_by(project_id=project.id, id=task_id)
    if task:
        taskruns = task_repo.filter_task_runs_by(task_id=task_id, project_id=project.id)
        results = [tr.dictize() for tr in taskruns]
        return Response(json.dumps(results), mimetype='application/json')
    else:
        return abort(404)


@blueprint.route('/<short_name>/tasks/')
@login_required
@admin_required
def tasks(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    title = project_title(project, "Tasks")

    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    pro = pro_features()
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
    return render_template('/projects/tasks.html',
                           title=title,
                           project=project,
                           owner=owner,
                           autoimporter_enabled=autoimporter_enabled,
                           n_tasks=n_tasks,
                           n_task_runs=n_task_runs,
                           overall_progress=overall_progress,
                           last_activity=last_activity,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                           n_volunteers=cached_projects.n_volunteers(project.get('id')),
                           pro_features=pro)


@blueprint.route('/<short_name>/tasks/browse', defaults={'page': 1})
@blueprint.route('/<short_name>/tasks/browse/<int:page>')
@login_required
@admin_required
def tasks_browse(short_name, page):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    title = project_title(project, "Tasks")
    n_volunteers = cached_projects.n_volunteers(project.id)
    n_completed_tasks = cached_projects.n_completed_tasks(project.id)
    pro = pro_features()

    def respond():
        per_page = 10
        offset = (page - 1) * per_page
        count = n_tasks
        project_tasks = cached_projects.browse_tasks(project.get('id'))
        page_tasks = project_tasks[offset:offset+per_page]
        if not page_tasks and page != 1:
            abort(404)

        pagination = Pagination(page, per_page, count)
        return render_template('/projects/tasks_browse.html',
                               project=project,
                               owner=owner,
                               tasks=page_tasks,
                               title=title,
                               pagination=pagination,
                               n_tasks=n_tasks,
                               overall_progress=overall_progress,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks,
                               pro_features=pro)
    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return respond()


@blueprint.route('/<short_name>/tasks/delete', methods=['GET', 'POST'])
@login_required
def delete_tasks(short_name):
    """Delete ALL the tasks for a given project"""
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)
    pro = pro_features()
    if request.method == 'GET':
        title = project_title(project, "Delete")
        n_volunteers = cached_projects.n_volunteers(project.id)
        n_completed_tasks = cached_projects.n_completed_tasks(project.id)
        project = add_custom_contrib_button_to(project, get_user_id_or_ip())
        return render_template('projects/tasks/delete.html',
                               project=project,
                               owner=owner,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks,
                               overall_progress=overall_progress,
                               last_activity=last_activity,
                               title=title,
                               pro_features=pro)
    else:
        task_repo.delete_valid_from_project(project)
        msg = gettext("Tasks and taskruns with no associated results have been deleted")
        flash(msg, 'success')
        return redirect(url_for('.tasks', short_name=project.short_name))


@blueprint.route('/<short_name>/tasks/export')
def export_to(short_name):
    """Export Tasks and TaskRuns in the given format"""
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    n_volunteers = cached_projects.n_volunteers(project.id)
    n_completed_tasks = cached_projects.n_completed_tasks(project.id)
    title = project_title(project, gettext("Export"))
    loading_text = gettext("Exporting data..., this may take a while")
    pro = pro_features()

    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    def respond():
        return render_template('/projects/export.html',
                               title=title,
                               loading_text=loading_text,
                               ckan_name=current_app.config.get('CKAN_NAME'),
                               project=project,
                               owner=owner,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks,
                               overall_progress=overall_progress,
                               pro_features=pro)

    def respond_json(ty):
        if ty not in ['task', 'task_run']:
            return abort(404)
        res = json_exporter.response_zip(project, ty)
        return res

    def respond_csv(ty):
        if ty not in ('task', 'task_run'):
            return abort(404)
        res = csv_exporter.response_zip(project, ty)
        return res

    def create_ckan_datastore(ckan, table, package_id, records):
        new_resource = ckan.resource_create(name=table,
                                            package_id=package_id)
        ckan.datastore_create(name=table,
                              resource_id=new_resource['result']['id'])
        ckan.datastore_upsert(name=table,
                              records=records,
                              resource_id=new_resource['result']['id'])

    def respond_ckan(ty):
        # First check if there is a package (dataset) in CKAN
        msg_1 = gettext("Data exported to ")
        msg = msg_1 + "%s ..." % current_app.config['CKAN_URL']
        ckan = Ckan(url=current_app.config['CKAN_URL'],
                    api_key=current_user.ckan_api)
        project_url = url_for('.details', short_name=project.short_name, _external=True)

        try:
            package, e = ckan.package_exists(name=project.short_name)
            records = json_exporter.gen_json(ty, project.id)
            if e:
                raise e
            if package:
                # Update the package
                owner = user_repo.get(project.owner_id)
                package = ckan.package_update(project=project, user=owner,
                                              url=project_url,
                                              resources=package['resources'])

                ckan.package = package
                resource_found = False
                for r in package['resources']:
                    if r['name'] == ty:
                        ckan.datastore_delete(name=ty, resource_id=r['id'])
                        ckan.datastore_create(name=ty, resource_id=r['id'])
                        ckan.datastore_upsert(name=ty,
                                              records=records,
                                              resource_id=r['id'])
                        resource_found = True
                        break
                if not resource_found:
                    create_ckan_datastore(ckan, ty, package['id'], records)
            else:
                owner = user_repo.get(project.owner_id)
                package = ckan.package_create(project=project, user=owner,
                                              url=project_url)
                create_ckan_datastore(ckan, ty, package['id'], records)
            flash(msg, 'success')
            return respond()
        except requests.exceptions.ConnectionError:
            msg = "CKAN server seems to be down, try again layer or contact the CKAN admins"
            current_app.logger.error(msg)
            flash(msg, 'danger')
        except Exception as inst:
            print inst
            if len(inst.args) == 3:
                t, msg, status_code = inst.args
                msg = ("Error: %s with status code: %s" % (t, status_code))
            else:  # pragma: no cover
                msg = ("Error: %s" % inst.args[0])
            current_app.logger.error(msg)
            flash(msg, 'danger')
        finally:
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
        project = add_custom_contrib_button_to(project, get_user_id_or_ip())
        return respond()

    if fmt not in export_formats:
        abort(415)

    if ty == 'task':
        task = task_repo.get_task_by(project_id=project.id)
        if task:
            ensure_authorized_to('read', task)
    if ty == 'task_run':
        task_run = task_repo.get_task_run_by(project_id=project.id)
        if task_run:
            ensure_authorized_to('read', task_run)

    return {"json": respond_json, "csv": respond_csv, 'ckan': respond_ckan}[fmt](ty)


@blueprint.route('/<short_name>/stats')
def show_stats(short_name):
    """Returns Project Stats"""
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    n_volunteers = cached_projects.n_volunteers(project.id)
    n_completed_tasks = cached_projects.n_completed_tasks(project.id)
    title = project_title(project, "Statistics")
    pro = pro_features(owner)

    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', project)

    if not ((n_tasks > 0) and (n_task_runs > 0)):
        project = add_custom_contrib_button_to(project, get_user_id_or_ip())
        return render_template('/projects/non_stats.html',
                               title=title,
                               project=project,
                               owner=owner,
                               n_tasks=n_tasks,
                               overall_progress=overall_progress,
                               n_volunteers=n_volunteers,
                               n_completed_tasks=n_completed_tasks,
                               pro_features=pro)

    dates_stats, hours_stats, users_stats = stats.get_stats(
        project.id,
        current_app.config['GEO'],
        period='2 week')
    total_contribs = (users_stats['n_anon'] + users_stats['n_auth'])
    if total_contribs > 0:
        anon_pct_taskruns = int((users_stats['n_anon'] * 100) / total_contribs)
        auth_pct_taskruns = 100 - anon_pct_taskruns
    else:
        anon_pct_taskruns = 0
        auth_pct_taskruns = 0

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
            pct_taskruns=auth_pct_taskruns,
            top5=users_stats['auth']['top5']))

    projectStats = dict(
        userStats=users_stats['users'],
        userAnonStats=users_stats['anon'],
        userAuthStats=users_stats['auth'],
        dayStats=dates_stats,
        hourStats=hours_stats)

    project_dict = add_custom_contrib_button_to(project, get_user_id_or_ip())
    contrib_time = cached_projects.average_contribution_time(project.id)
    formatted_contrib_time = round(contrib_time.total_seconds(), 2)

    return render_template(
        '/projects/stats.html',
        title=title,
        projectStats=json.dumps(projectStats),
        userStats=userStats,
        project=project_dict,
        owner=owner,
        n_tasks=n_tasks,
        overall_progress=overall_progress,
        n_volunteers=n_volunteers,
        n_completed_tasks=n_completed_tasks,
        avg_contrib_time=formatted_contrib_time,
        pro_features=pro)


@blueprint.route('/<short_name>/tasks/settings')
@login_required
@admin_required
def task_settings(short_name):
    """Settings page for tasks of the project"""
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    n_volunteers = cached_projects.n_volunteers(project.id)
    n_completed_tasks = cached_projects.n_completed_tasks(project.id)
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)
    pro = pro_features()
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('projects/task_settings.html',
                           project=project,
                           owner=owner,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           n_volunteers=n_volunteers,
                           n_completed_tasks=n_completed_tasks,
                           pro_features=pro)


@blueprint.route('/<short_name>/tasks/redundancy', methods=['GET', 'POST'])
@login_required
@admin_required
def task_n_answers(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    title = project_title(project, gettext('Redundancy'))
    form = TaskRedundancyForm()
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)
    pro = pro_features()
    if request.method == 'GET':

        # Set the form's task redundancy value to the currently set value.
        task_redundancy_num = task_repo.get_tasks_redundancy(project)
        form.n_answers.data = str(task_redundancy_num)

        return render_template('/projects/task_n_answers.html',
                               title=title,
                               form=form,
                               project=project,
                               owner=owner,
                               pro_features=pro)
    elif request.method == 'POST' and form.validate():
        task_repo.update_tasks_redundancy(project, form.n_answers.data)
        # Log it
        auditlogger.log_event(project, current_user, 'update', 'task.n_answers',
                              'N/A', form.n_answers.data)
        msg = gettext('Redundancy of Tasks updated!')
        flash(msg, 'success')
        return redirect(url_for('.tasks', short_name=project.short_name))
    else:
        flash(gettext('Please correct the errors'), 'error')
        return render_template('/projects/task_n_answers.html',
                               title=title,
                               form=form,
                               project=project,
                               owner=owner,
                               pro_features=pro)


@blueprint.route('/<short_name>/tasks/scheduler', methods=['GET', 'POST'])
@login_required
@admin_required
def task_scheduler(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    title = project_title(project, gettext('Task Scheduler'))
    form = TaskSchedulerForm()
    pro = pro_features()

    def respond():
        return render_template('/projects/task_scheduler.html',
                               title=title,
                               form=form,
                               project=project,
                               owner=owner,
                               pro_features=pro)
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)

    if request.method == 'GET':
        if project.info.get('sched'):
            for s in form.sched.choices:
                if project.info['sched'] == s[0]:
                    form.sched.data = s[0]
                    break
        return respond()

    if request.method == 'POST' and form.validate():
        project = project_repo.get_by_shortname(short_name=project.short_name)
        if project.info.get('sched'):
            old_sched = project.info['sched']
        else:
            old_sched = 'default'
        if form.sched.data:
            project.info['sched'] = form.sched.data
        project_repo.save(project)
        # Log it
        if old_sched != project.info['sched']:
            auditlogger.log_event(project, current_user, 'update', 'sched',
                                  old_sched, project.info['sched'])
        msg = gettext("Project Task Scheduler updated!")
        flash(msg, 'success')

        return redirect(url_for('.tasks', short_name=project.short_name))
    else:  # pragma: no cover
        flash(gettext('Please correct the errors'), 'error')
        return respond()


@blueprint.route('/<short_name>/tasks/priority', methods=['GET', 'POST'])
@login_required
@admin_required
def task_priority(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    title = project_title(project, gettext('Task Priority'))
    form = TaskPriorityForm()
    pro = pro_features()

    def respond():
        return render_template('/projects/task_priority.html',
                               title=title,
                               form=form,
                               project=project,
                               owner=owner,
                               pro_features=pro)
    ensure_authorized_to('read', project)
    ensure_authorized_to('update', project)

    if request.method == 'GET':
        return respond()
    if request.method == 'POST' and form.validate():
        for task_id in form.task_ids.data.split(","):
            if task_id != '':
                t = task_repo.get_task_by(project_id=project.id, id=int(task_id))
                if t:
                    old_priority = t.priority_0
                    t.priority_0 = form.priority_0.data
                    task_repo.update(t)

                    if old_priority != t.priority_0:
                        old_value = json.dumps({'task_id': t.id,
                                                'task_priority_0': old_priority})
                        new_value = json.dumps({'task_id': t.id,
                                                'task_priority_0': t.priority_0})
                        auditlogger.log_event(project, current_user, 'update',
                                              'task.priority_0',
                                              old_value, new_value)
                else:  # pragma: no cover
                    flash(gettext(("Ooops, Task.id=%s does not belong to the project" % task_id)), 'danger')
        flash(gettext("Task priority has been changed"), 'success')
        return respond()
    else:
        flash(gettext('Please correct the errors'), 'error')
        return respond()


@blueprint.route('/<short_name>/blog')
def show_blogposts(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    blogposts = blog_repo.filter_by(project_id=project.id)
    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', Blogpost, project_id=project.id)
    pro = pro_features()
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('projects/blog.html', project=project,
                           owner=owner, blogposts=blogposts,
                           overall_progress=overall_progress,
                           n_tasks=n_tasks,
                           n_task_runs=n_task_runs,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                           n_volunteers=cached_projects.n_volunteers(project.get('id')),
                           pro_features=pro)


@blueprint.route('/<short_name>/<int:id>')
def show_blogpost(short_name, id):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    blogpost = blog_repo.get_by(id=id, project_id=project.id)
    if blogpost is None:
        raise abort(404)
    if project.needs_password():
        redirect_to_password = _check_if_redirect_to_password(project)
        if redirect_to_password:
            return redirect_to_password
    else:
        ensure_authorized_to('read', blogpost)
    pro = pro_features()
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('projects/blog_post.html',
                           project=project,
                           owner=owner,
                           blogpost=blogpost,
                           overall_progress=overall_progress,
                           n_tasks=n_tasks,
                           n_task_runs=n_task_runs,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                           n_volunteers=cached_projects.n_volunteers(project.get('id')),
                           pro_features=pro)


@blueprint.route('/<short_name>/new-blogpost', methods=['GET', 'POST'])
@login_required
@admin_required
def new_blogpost(short_name):
    pro = pro_features()

    def respond():
        dict_project = add_custom_contrib_button_to(project, get_user_id_or_ip())
        return render_template('projects/new_blogpost.html',
                               title=gettext("Write a new post"),
                               form=form,
                               project=dict_project,
                               owner=owner,
                               overall_progress=overall_progress,
                               n_tasks=n_tasks,
                               n_task_runs=n_task_runs,
                               n_completed_tasks=cached_projects.n_completed_tasks(dict_project.get('id')),
                               n_volunteers=cached_projects.n_volunteers(dict_project.get('id')),
                               pro_features=pro)

    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    form = BlogpostForm(request.form)
    del form.id

    if request.method != 'POST':
        ensure_authorized_to('create', Blogpost, project_id=project.id)
        return respond()

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond()

    blogpost = Blogpost(title=form.title.data,
                        body=form.body.data,
                        user_id=current_user.id,
                        project_id=project.id)
    ensure_authorized_to('create', blogpost)
    blog_repo.save(blogpost)
    cached_projects.delete_project(short_name)

    msg_1 = gettext('Blog post created!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')

    return redirect(url_for('.show_blogposts', short_name=short_name))


@blueprint.route('/<short_name>/<int:id>/update', methods=['GET', 'POST'])
@login_required
@admin_required
def update_blogpost(short_name, id):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    pro = pro_features()
    blogpost = blog_repo.get_by(id=id, project_id=project.id)
    if blogpost is None:
        raise abort(404)

    def respond():
        return render_template('projects/update_blogpost.html',
                               title=gettext("Edit a post"),
                               form=form, project=project, owner=owner,
                               blogpost=blogpost,
                               overall_progress=overall_progress,
                               n_task_runs=n_task_runs,
                               n_completed_tasks=cached_projects.n_completed_tasks(project.id),
                               n_volunteers=cached_projects.n_volunteers(project.id),
                               pro_features=pro)

    form = BlogpostForm()

    if request.method != 'POST':
        ensure_authorized_to('update', blogpost)
        form = BlogpostForm(obj=blogpost)
        return respond()

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond()

    ensure_authorized_to('update', blogpost)
    blogpost = Blogpost(id=form.id.data,
                        title=form.title.data,
                        body=form.body.data,
                        user_id=current_user.id,
                        project_id=project.id)
    blog_repo.update(blogpost)
    cached_projects.delete_project(short_name)

    msg_1 = gettext('Blog post updated!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')

    return redirect(url_for('.show_blogposts', short_name=short_name))


@blueprint.route('/<short_name>/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_blogpost(short_name, id):
    project = project_by_shortname(short_name)[0]
    blogpost = blog_repo.get_by(id=id, project_id=project.id)
    if blogpost is None:
        raise abort(404)

    ensure_authorized_to('delete', blogpost)
    blog_repo.delete(blogpost)
    cached_projects.delete_project(short_name)
    flash('<i class="icon-ok"></i> ' + 'Blog post deleted!', 'success')
    return redirect(url_for('.show_blogposts', short_name=short_name))


def _check_if_redirect_to_password(project):
    cookie_exp = current_app.config.get('PASSWD_COOKIE_TIMEOUT')
    passwd_mngr = ProjectPasswdManager(CookieHandler(request, signer, cookie_exp))
    if passwd_mngr.password_needed(project, get_user_id_or_ip()):
        return redirect(url_for('.password_required',
                                short_name=project.short_name, next=request.path))


@blueprint.route('/<short_name>/auditlog')
@login_required
@admin_required
def auditlog(short_name):
    pro = pro_features()
    if not pro['auditlog_enabled']:
        raise abort(403)

    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    ensure_authorized_to('read', Auditlog, project_id=project.id)
    logs = auditlogger.get_project_logs(project.id)
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('projects/auditlog.html', project=project,
                           owner=owner, logs=logs,
                           overall_progress=overall_progress,
                           n_tasks=n_tasks,
                           n_task_runs=n_task_runs,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                           n_volunteers=cached_projects.n_volunteers(project.get('id')),
                           pro_features=pro)


@blueprint.route('/<short_name>/publish', methods=['GET', 'POST'])
@login_required
@admin_required
def publish(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    pro = pro_features()
    ensure_authorized_to('publish', project)
    if request.method == 'GET':
        return render_template('projects/publish.html',
                                project=project,
                                pro_features=pro)
    project.published = True
    project_repo.save(project)
    task_repo.delete_taskruns_from_project(project)
    auditlogger.log_event(project, current_user, 'update', 'published', False, True)
    flash(gettext('Project published! Volunteers will now be able to help you!'))
    return redirect(url_for('.details', short_name=project.short_name))


def project_event_stream(short_name, channel_type):
    """Event stream for pub/sub notifications."""
    pubsub = sentinel.master.pubsub()
    channel = "channel_%s_%s" % (channel_type, short_name)
    pubsub.subscribe(channel)
    for message in pubsub.listen():
        yield 'data: %s\n\n' % message['data']


@blueprint.route('/<short_name>/privatestream')
@login_required
@admin_required
def project_stream_uri_private(short_name):
    """Returns stream."""
    if current_app.config.get('SSE'):
        (project, owner, n_tasks, n_task_runs,
         overall_progress, last_activity,
         n_results) = project_by_shortname(short_name)
        if (current_user.id == project.owner_id or current_user.admin):
            return Response(project_event_stream(short_name, 'private'),
                            mimetype="text/event-stream",
                            direct_passthrough=True)
        else:
            return abort(403)
    else:
        return abort(404)


@blueprint.route('/<short_name>/publicstream')
def project_stream_uri_public(short_name):
    """Returns stream."""
    if current_app.config.get('SSE'):
        (project, owner, n_tasks, n_task_runs,
         overall_progress, last_activity,
         n_results) = project_by_shortname(short_name)
        return Response(project_event_stream(short_name, 'public'),
                        mimetype="text/event-stream")
    else:
        abort(404)


@blueprint.route('/<short_name>/webhook', defaults={'oid': None})
@blueprint.route('/<short_name>/webhook/<int:oid>', methods=['GET', 'POST'])
@login_required
@admin_required
def webhook_handler(short_name, oid=None):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    pro = pro_features()
    if not pro['webhooks_enabled']:
        raise abort(403)

    responses = webhook_repo.filter_by(project_id=project.id)
    if request.method == 'POST' and oid:
        tmp = webhook_repo.get(oid)
        if tmp:
            webhook_queue.enqueue(webhook, project.webhook,
                                  tmp.payload, tmp.id)
            return json.dumps(tmp.dictize())
        else:
            abort(404)

    ensure_authorized_to('read', Webhook, project_id=project.id)
    redirect_to_password = _check_if_redirect_to_password(project)
    if redirect_to_password:
        return redirect_to_password
    project = add_custom_contrib_button_to(project, get_user_id_or_ip())
    return render_template('projects/webhook.html', project=project,
                           owner=owner, responses=responses,
                           overall_progress=overall_progress,
                           n_tasks=n_tasks,
                           n_task_runs=n_task_runs,
                           n_completed_tasks=cached_projects.n_completed_tasks(project.get('id')),
                           n_volunteers=cached_projects.n_volunteers(project.get('id')),
                           pro_features=pro)


@blueprint.route('/<short_name>/results')
def results(short_name):
    """Results page for the project."""
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)

    title = project_title(project, "Results")

    ensure_authorized_to('read', project)

    return render_template('/projects/results.html',
                           title=title, project=project, owner=owner,
                           n_results=n_results)
