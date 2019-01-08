# -* -coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""Admin view for PYBOSSA."""
import sys
from rq import Queue
from flask import Blueprint
from flask import render_template
from flask import request
from flask import abort
from flask import flash
from flask import redirect
from flask import url_for
from flask import current_app
from flask import Response
from flask import Markup
from flask_login import login_required, current_user
from flask_babel import gettext
from flask_wtf.csrf import generate_csrf
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import ProgrammingError
import pandas as pd

from pybossa.model.category import Category
from pybossa.model.announcement import Announcement
from pybossa.util import admin_required, handle_content_type
from pybossa.util import redirect_content_type
from pybossa.cache import projects as cached_projects
from pybossa.cache import categories as cached_cat
from pybossa.auth import ensure_authorized_to
from pybossa.core import announcement_repo, project_repo, user_repo, sentinel
from pybossa.feed import get_update_feed
import pybossa.dashboard.data as dashb
from pybossa.jobs import get_dashboard_jobs
import json
from io import StringIO

from pybossa.forms.admin_view_forms import *
from pybossa.news import NOTIFY_ADMIN


blueprint = Blueprint('admin', __name__)

DASHBOARD_QUEUE = Queue('super', connection=sentinel.master)

def format_error(msg, status_code):
    """Return error as a JSON response."""
    error = dict(error=msg,
                 status_code=status_code)
    return Response(json.dumps(error), status=status_code,
                    mimetype='application/json')


@blueprint.route('/')
@login_required
@admin_required
def index():
    """List admin actions."""
    key = NOTIFY_ADMIN + str(current_user.id)
    sentinel.master.delete(key)
    return handle_content_type(dict(template='/admin/index.html'))


@blueprint.route('/featured')
@blueprint.route('/featured/<int:project_id>', methods=['POST', 'DELETE'])
@login_required
@admin_required
def featured(project_id=None):
    """List featured projects of PYBOSSA."""
    try:
        if request.method == 'GET':
            categories = cached_cat.get_all()
            projects = {}
            for c in categories:
                n_projects = cached_projects.n_count(category=c.short_name)
                projects[c.short_name] = cached_projects.get(
                    category=c.short_name,
                    page=1,
                    per_page=n_projects)
            response = dict(template = '/admin/projects.html',
                            projects=projects,
                            categories=categories,
                            form=dict(csrf=generate_csrf()))
            return handle_content_type(response)
        else:
            project = project_repo.get(project_id)
            if project:
                ensure_authorized_to('update', project)
                if request.method == 'POST':
                    if project.featured is True:
                        msg = "Project.id %s already featured" % project_id
                        return format_error(msg, 415)
                    cached_projects.reset()
                    project.featured = True
                    project_repo.update(project)
                    return json.dumps(project.dictize())

                if request.method == 'DELETE':
                    if project.featured is False:
                        msg = 'Project.id %s is not featured' % project_id
                        return format_error(msg, 415)
                    cached_projects.reset()
                    project.featured = False
                    project_repo.update(project)
                    return json.dumps(project.dictize())
            else:
                msg = 'Project.id %s not found' % project_id
                return format_error(msg, 404)
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users(user_id=None):
    """Manage users of PYBOSSA."""
    form = SearchForm(request.body)
    users = [user for user in user_repo.filter_by(admin=True)
             if user.id != current_user.id]

    if request.method == 'POST' and form.user.data:
        query = form.user.data
        found = [user for user in user_repo.search_by_name(query)
                 if user.id != current_user.id]
        [ensure_authorized_to('update', found_user) for found_user in found]
        if not found:
            markup = Markup('<strong>{}</strong> {} <strong>{}</strong>')
            flash(markup.format(gettext("Ooops!"),
                                gettext("We didn't find a user matching your query:"),
                                form.user.data))
        response = dict(template='/admin/users.html', found=found, users=users,
                        title=gettext("Manage Admin Users"),
                        form=form)
        return handle_content_type(response)

    response = dict(template='/admin/users.html', found=[], users=users,
                    title=gettext("Manage Admin Users"), form=form)
    return handle_content_type(response)


@blueprint.route('/users/export')
@login_required
@admin_required
def export_users():
    """Export Users list in the given format, only for admins."""
    exportable_attributes = ('id', 'name', 'fullname', 'email_addr',
                             'created', 'locale', 'admin', 'consent',
                             'restrict')

    def respond_json():
        tmp = 'attachment; filename=all_users.json'
        res = Response(gen_json(), mimetype='application/json')
        res.headers['Content-Disposition'] = tmp
        return res

    def gen_json():
        users = user_repo.filter_by(restrict=False)
        json_users = []
        for user in users:
            json_users.append(dictize_with_exportable_attributes(user))
        return json.dumps(json_users)

    def dictize_with_exportable_attributes(user):
        dict_user = {}
        for attr in exportable_attributes:
            dict_user[attr] = getattr(user, attr)
        return dict_user

    def respond_csv():
        tmp = 'attachment; filename=all_users.csv'
        dict_users = []
        for user in user_repo.filter_by(restrict=False):
            dict_users.append(user.dictize())
        df = pd.DataFrame.from_dict(dict_users)
        res = Response(df.to_csv(columns=exportable_attributes,
                                 index=False),
                       mimetype='text/csv')
        res.headers['Content-Disposition'] = tmp
        return res

    export_formats = ["json", "csv"]

    fmt = request.args.get('format')
    if not fmt:
        return redirect(url_for('.index'))
    if fmt not in export_formats:
        abort(415)
    return {"json": respond_json, "csv": respond_csv}[fmt]()


@blueprint.route('/users/add/<int:user_id>')
@login_required
@admin_required
def add_admin(user_id=None):
    """Add admin flag for user_id."""
    try:
        if user_id:
            user = user_repo.get(user_id)
            if user:
                ensure_authorized_to('update', user)
                user.admin = True
                user_repo.update(user)
                return redirect_content_type(url_for(".users"))
            else:
                msg = "User not found"
                return format_error(msg, 404)
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/users/del/<int:user_id>')
@login_required
@admin_required
def del_admin(user_id=None):
    """Del admin flag for user_id."""
    try:
        if user_id:
            user = user_repo.get(user_id)
            if user:
                ensure_authorized_to('update', user)
                user.admin = False
                user_repo.update(user)
                return redirect_content_type(url_for('.users'))
            else:
                msg = "User.id not found"
                return format_error(msg, 404)
        else:  # pragma: no cover
            msg = "User.id is missing for method del_admin"
            return format_error(msg, 415)
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    """List Categories."""
    try:
        if request.method == 'GET':
            ensure_authorized_to('read', Category)
            form = CategoryForm()
        if request.method == 'POST':
            ensure_authorized_to('create', Category)
            form = CategoryForm(request.body)
            del form.id
            if form.validate():
                slug = form.name.data.lower().replace(" ", "")
                category = Category(name=form.name.data,
                                    short_name=slug,
                                    description=form.description.data)
                project_repo.save_category(category)
                cached_cat.reset()
                msg = gettext("Category added")
                flash(msg, 'success')
            else:
                flash(gettext('Please correct the errors'), 'error')
        categories = cached_cat.get_all()
        n_projects_per_category = dict()
        for c in categories:
            n_projects_per_category[c.short_name] = \
                cached_projects.n_count(c.short_name)

        response = dict(template='admin/categories.html',
                        title=gettext('Categories'),
                        categories=categories,
                        n_projects_per_category=n_projects_per_category,
                        form=form)
        return handle_content_type(response)
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/categories/del/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def del_category(id):
    """Delete a category."""
    try:
        category = project_repo.get_category(id)
        if category:
            if len(cached_cat.get_all()) > 1:
                ensure_authorized_to('delete', category)
                if request.method == 'GET':
                    response = dict(template='admin/del_category.html',
                                    title=gettext('Delete Category'),
                                    category=category,
                                    form=dict(csrf=generate_csrf()))
                    return handle_content_type(response)
                if request.method == 'POST':
                    project_repo.delete_category(category)
                    msg = gettext("Category deleted")
                    flash(msg, 'success')
                    cached_cat.reset()
                    return redirect_content_type(url_for(".categories"))
            else:
                msg = gettext('Sorry, it is not possible to delete the only'
                              ' available category. You can modify it, '
                              ' click the edit button')
                flash(msg, 'warning')
                return redirect_content_type(url_for('.categories'))
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/categories/update/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_category(id):
    """Update a category."""
    try:
        category = project_repo.get_category(id)
        if category:
            ensure_authorized_to('update', category)
            form = CategoryForm(obj=category)
            form.populate_obj(category)
            if request.method == 'GET':
                response = dict(template='admin/update_category.html',
                                title=gettext('Update Category'),
                                category=category,
                                form=form)
                return handle_content_type(response)
            if request.method == 'POST':
                form = CategoryForm(request.body)
                if form.validate():
                    slug = form.name.data.lower().replace(" ", "")
                    new_category = Category(id=form.id.data,
                                            name=form.name.data,
                                            short_name=slug)
                    project_repo.update_category(new_category)
                    cached_cat.reset()
                    msg = gettext("Category updated")
                    flash(msg, 'success')
                    return redirect_content_type(url_for(".categories"))
                else:
                    msg = gettext("Please correct the errors")
                    flash(msg, 'success')
                    response = dict(template='admin/update_category.html',
                                    title=gettext('Update Category'),
                                    category=category,
                                    form=form)
                    return handle_content_type(response)
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/announcement', methods=['GET'])
@login_required
@admin_required
def announcement():
    """Manage anncounements."""
    announcements = announcement_repo.get_all_announcements()
    response = dict(template='admin/announcement.html',
                    title=gettext("Manage global Announcements"),
                    announcements=announcements,
                    csrf=generate_csrf())
    return handle_content_type(response)


@blueprint.route('/announcement/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_announcement():
    """Create new announcement."""
    def respond():
        response = dict(template='admin/new_announcement.html',
                        title=gettext("Write a new post"),
                        form=form)
        return handle_content_type(response)

    form = AnnouncementForm()
    del form.id

    # project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)

    if request.method != 'POST':
        ensure_authorized_to('create', Announcement())
        return respond()

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond()

    announcement = Announcement(title=form.title.data,
                                body=form.body.data,
                                published=form.published.data,
                                media_url=form.media_url.data,
                                user_id=current_user.id)
    ensure_authorized_to('create', announcement)
    announcement_repo.save(announcement)

    msg_1 = gettext('Annnouncement created!')
    markup = Markup('<i class="icon-ok"></i> {}')
    flash(markup.format(msg_1), 'success')

    return redirect_content_type(url_for('admin.announcement'))


@blueprint.route('/announcement/<int:id>/update', methods=['GET', 'POST'])
@login_required
@admin_required
def update_announcement(id):
    announcement = announcement_repo.get_by(id=id)
    if announcement is None:
        raise abort(404)

    def respond():
        response = dict(template='admin/new_announcement.html',
                        title=gettext("Edit a post"),
                        form=form)
        return handle_content_type(response)

    form = AnnouncementForm()

    if request.method != 'POST':
        ensure_authorized_to('update', announcement)
        form = AnnouncementForm(obj=announcement)
        return respond()

    if not form.validate():
        flash(gettext('Please correct the errors'), 'error')
        return respond()

    ensure_authorized_to('update', announcement)
    announcement = Announcement(id=form.id.data,
                                title=form.title.data,
                                body=form.body.data,
                                published=form.published.data,
                                media_url=form.media_url.data,
                                user_id=current_user.id)
    announcement_repo.update(announcement)

    msg_1 = gettext('Announcement updated!')
    markup = Markup('<i class="icon-ok"></i> {}')
    flash(markup.format(msg_1), 'success')

    return redirect_content_type(url_for('admin.announcement'))


@blueprint.route('/announcement/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(id):
    announcement = announcement_repo.get_by(id=id)
    if announcement is None:
        raise abort(404)

    ensure_authorized_to('delete', announcement)
    announcement_repo.delete(announcement)
    msg_1 = gettext('Announcement deleted!')
    markup = Markup('<i class="icon-ok"></i> {}')
    flash(markup.format(msg_1), 'success')
    return redirect_content_type(url_for('admin.announcement'))


@blueprint.route('/dashboard/')
@login_required
@admin_required
def dashboard():
    """Show PYBOSSA Dashboard."""
    try:
        if request.args.get('refresh') == '1':
            db_jobs = get_dashboard_jobs()
            for j in db_jobs:
                DASHBOARD_QUEUE.enqueue(j['name'])
            msg = gettext('Dashboard jobs enqueued,'
                          ' refresh page in a few minutes')
            flash(msg)
        active_users_last_week = dashb.format_users_week()
        active_anon_last_week = dashb.format_anon_week()
        draft_projects_last_week = dashb.format_draft_projects()
        published_projects_last_week = dashb.format_published_projects()
        update_projects_last_week = dashb.format_update_projects()
        new_tasks_week = dashb.format_new_tasks()
        new_task_runs_week = dashb.format_new_task_runs()
        new_users_week = dashb.format_new_users()
        returning_users_week = dashb.format_returning_users()
        update_feed = get_update_feed()

        response = dict(
            template='admin/dashboard.html',
            title=gettext('Dashboard'),
            active_users_last_week=active_users_last_week,
            active_anon_last_week=active_anon_last_week,
            draft_projects_last_week=draft_projects_last_week,
            published_projects_last_week=published_projects_last_week,
            update_projects_last_week=update_projects_last_week,
            new_tasks_week=new_tasks_week,
            new_task_runs_week=new_task_runs_week,
            new_users_week=new_users_week,
            returning_users_week=returning_users_week,
            update_feed=update_feed,
            wait=False)
        return handle_content_type(response)
    except ProgrammingError as e:
        response = dict(template='admin/dashboard.html',
                        title=gettext('Dashboard'),
                        wait=True)
        return handle_content_type(response)
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)
