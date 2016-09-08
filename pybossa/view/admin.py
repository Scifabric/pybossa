# -* -coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
"""Admin view for PyBossa."""
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
from flask.ext.login import login_required, current_user
from flask.ext.babel import gettext
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import ProgrammingError

from pybossa.model.category import Category
from pybossa.util import admin_required, UnicodeWriter
from pybossa.cache import projects as cached_projects
from pybossa.cache import categories as cached_cat
from pybossa.auth import ensure_authorized_to
from pybossa.core import project_repo, user_repo, sentinel
from pybossa.feed import get_update_feed
import pybossa.dashboard.data as dashb
from pybossa.jobs import get_dashboard_jobs
import json
from StringIO import StringIO

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
    return render_template('/admin/index.html')


@blueprint.route('/tile-generator')
@login_required
@admin_required
def map_tile_generator():
    return render_template('/admin/map-tile-generator.html')

@blueprint.route('/map-result')
@login_required
@admin_required
def map_result():
    all_projects = project_repo.get_all()
    return render_template('/admin/map_result.html', all_projects=all_projects)

@blueprint.route('/featured')
@blueprint.route('/featured/<int:project_id>', methods=['POST', 'DELETE'])
@login_required
@admin_required
def featured(project_id=None):
    """List featured projects of PyBossa."""
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
            return render_template('/admin/projects.html',
                                   projects=projects,
                                   categories=categories)
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
    """Manage users of PyBossa."""
    form = SearchForm(request.form)
    users = [user for user in user_repo.filter_by(admin=True)
             if user.id != current_user.id]

    if request.method == 'POST' and form.user.data:
        query = form.user.data
        found = [user for user in user_repo.search_by_name(query)
                 if user.id != current_user.id]
        [ensure_authorized_to('update', found_user) for found_user in found]
        if not found:
            flash("<strong>Ooops!</strong> We didn't find a user "
                  "matching your query: <strong>%s</strong>" % form.user.data)
        return render_template('/admin/users.html', found=found, users=users,
                               title=gettext("Manage Admin Users"),
                               form=form)

    return render_template('/admin/users.html', found=[], users=users,
                           title=gettext("Manage Admin Users"), form=form)


@blueprint.route('/users/export')
@login_required
@admin_required
def export_users():
    """Export Users list in the given format, only for admins."""
    exportable_attributes = ('id', 'name', 'fullname', 'email_addr',
                             'created', 'locale', 'admin','country','newsletter_subscribe', 'task_contributions')

    def respond_json():
        tmp = 'attachment; filename=all_users.json'
        res = Response(gen_json(), mimetype='application/json')
        res.headers['Content-Disposition'] = tmp
        return res

    def gen_json():
        users = user_repo.get_all()
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
        out = StringIO()
        writer = UnicodeWriter(out)
        tmp = 'attachment; filename=all_users.csv'
        res = Response(gen_csv(out, writer, write_user), mimetype='text/csv')
        res.headers['Content-Disposition'] = tmp
        return res

    def gen_csv(out, writer, write_user):
        add_headers(writer)
        for user in user_repo.get_all():
            write_user(writer, user)
        yield out.getvalue()

    def write_user(writer, user):
        values = [getattr(user, attr) for attr in sorted(exportable_attributes)]
        writer.writerow(values)

    def add_headers(writer):
        writer.writerow(sorted(exportable_attributes))

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
                return redirect(url_for(".users"))
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
                return redirect(url_for('.users'))
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
            form = CategoryForm(request.form)
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

        return render_template('admin/categories.html',
                               title=gettext('Categories'),
                               categories=categories,
                               n_projects_per_category=n_projects_per_category,
                               form=form)
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
                    return render_template('admin/del_category.html',
                                           title=gettext('Delete Category'),
                                           category=category)
                if request.method == 'POST':
                    project_repo.delete_category(category)
                    msg = gettext("Category deleted")
                    flash(msg, 'success')
                    cached_cat.reset()
                    return redirect(url_for(".categories"))
            else:
                msg = gettext('Sorry, it is not possible to delete the only'
                              ' available category. You can modify it, '
                              ' click the edit button')
                flash(msg, 'warning')
                return redirect(url_for('.categories'))
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
                return render_template('admin/update_category.html',
                                       title=gettext('Update Category'),
                                       category=category,
                                       form=form)
            if request.method == 'POST':
                form = CategoryForm(request.form)
                if form.validate():
                    slug = form.name.data.lower().replace(" ", "")
                    new_category = Category(id=form.id.data,
                                            name=form.name.data,
                                            short_name=slug)
                    project_repo.update_category(new_category)
                    cached_cat.reset()
                    msg = gettext("Category updated")
                    flash(msg, 'success')
                    return redirect(url_for(".categories"))
                else:
                    msg = gettext("Please correct the errors")
                    flash(msg, 'success')
                    return render_template('admin/update_category.html',
                                           title=gettext('Update Category'),
                                           category=category,
                                           form=form)
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/dashboard/')
@login_required
@admin_required
def dashboard():
    """Show PyBossa Dashboard."""
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

        return render_template(
            'admin/dashboard.html',
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
    except ProgrammingError as e:
        return render_template('admin/dashboard.html',
                               title=gettext('Dashboard'),
                               wait=True)
    except Exception as e:  # pragma: no cover
        current_app.logger.error(e)
        return abort(500)
