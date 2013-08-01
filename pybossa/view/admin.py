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
from flaskext.wtf import Form, TextField, IntegerField, HiddenInput, validators
from flask.ext.babel import lazy_gettext, gettext
from werkzeug.exceptions import HTTPException

import pybossa.model as model
from pybossa.core import db
from pybossa.util import admin_required
from pybossa.cache import apps as cached_apps
from pybossa.cache import categories as cached_cat
from pybossa.auth import require
import pybossa.validator as pb_validator
from sqlalchemy import or_, func
import json


blueprint = Blueprint('admin', __name__)


def format_error(msg, status_code):
    error = dict(error=msg,
                 status_code=status_code)
    return Response(json.dumps(error), status=status_code,
                    mimetype='application/json')


@blueprint.route('/')
@login_required
@admin_required
def index():
    """List admin actions"""
    return render_template('/admin/index.html')


@blueprint.route('/featured')
@blueprint.route('/featured/<int:app_id>', methods=['POST', 'DELETE'])
@login_required
@admin_required
def featured(app_id=None):
    """List featured apps of PyBossa"""
    try:
        categories = cached_cat.get_all()

        if request.method == 'GET':
            apps = {}
            for c in categories:
                n_apps = cached_apps.n_count(category=c.short_name)
                apps[c.short_name], n_apps = cached_apps.get(category=c.short_name,
                                                             page=1,
                                                             per_page=n_apps)
            return render_template('/admin/applications.html', apps=apps,
                                   categories=categories)
        elif app_id:
            if request.method == 'POST':
                cached_apps.reset()
                f = model.Featured()
                f.app_id = app_id
                app = db.session.query(model.App).get(app_id)
                require.app.update(app)
                # Check if the app is already in this table
                tmp = db.session.query(model.Featured)\
                        .filter(model.Featured.app_id == app_id)\
                        .first()
                if (tmp is None):
                    db.session.add(f)
                    db.session.commit()
                    return json.dumps(f.dictize())
                else:
                    msg = "App.id %s alreay in Featured table" % app_id
                    return format_error(msg, 415)
            if request.method == 'DELETE':
                cached_apps.reset()
                f = db.session.query(model.Featured)\
                      .filter(model.Featured.app_id == app_id)\
                      .first()
                if (f):
                    db.session.delete(f)
                    db.session.commit()
                    return "", 204
                else:
                    msg = 'App.id %s is not in Featured table' % app_id
                    return format_error(msg, 404)
        else:
            msg = ('App.id is missing for %s action in featured method' %
                   request.method)
            return format_error(msg, 415)
    except HTTPException:
        return abort(403)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)


class SearchForm(Form):
    user = TextField(lazy_gettext('User'))


@blueprint.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users(user_id=None):
    """Manage users of PyBossa"""
    try:
        form = SearchForm(request.form)
        users = db.session.query(model.User)\
                  .filter(model.User.admin == True)\
                  .filter(model.User.id != current_user.id)\
                  .all()

        if request.method == 'POST' and form.user.data:
            query = '%' + form.user.data.lower() + '%'
            found = db.session.query(model.User)\
                      .filter(or_(func.lower(model.User.name).like(query),
                                  func.lower(model.User.fullname).like(query)))\
                      .filter(model.User.id != current_user.id)\
                      .all()
            require.user.update(found)
            if not found:
                flash("<strong>Ooops!</strong> We didn't find a user "
                      "matching your query: <strong>%s</strong>" % form.user.data)
            return render_template('/admin/users.html', found=found, users=users,
                                   title=gettext("Manage Admin Users"),
                                   form=form)

        return render_template('/admin/users.html', found=[], users=users,
                               title=gettext("Manage Admin Users"), form=form)
    except HTTPException:
        return abort(403)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/users/add/<int:user_id>')
@login_required
@admin_required
def add_admin(user_id=None):
    """Add admin flag for user_id"""
    try:
        if user_id:
            user = db.session.query(model.User)\
                     .get(user_id)
            require.user.update(user)
            if user:
                user.admin = True
                db.session.commit()
                return redirect(url_for(".users"))
            else:
                msg = "User not found"
                return format_error(msg, 404)
    except HTTPException:
        return abort(403)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/users/del/<int:user_id>')
@login_required
@admin_required
def del_admin(user_id=None):
    """Del admin flag for user_id"""
    try:
        if user_id:
            user = db.session.query(model.User)\
                     .get(user_id)
            require.user.update(user)
            if user:
                user.admin = False
                db.session.commit()
                return redirect(url_for('.users'))
            else:
                msg = "User.id not found"
                return format_error(msg, 404)
        else:
            msg = "User.id is missing for method del_admin"
            return format_error(msg, 415)
    except HTTPException:
        return abort(403)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)


class CategoryForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(db.session, model.Category, model.Category.name,
                                          message="Name is already taken.")])
    description = TextField(lazy_gettext('Description'),
                            [validators.Required()])


@blueprint.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    """List Categories"""
    try:
        if request.method == 'GET':
            require.category.read()
            form = CategoryForm()
        if request.method == 'POST':
            require.category.create()
            form = CategoryForm(request.form)
            if form.validate():
                slug = form.name.data.lower().replace(" ", "")
                category = model.Category(name=form.name.data,
                                          short_name=slug,
                                          description=form.description.data)
                db.session.add(category)
                db.session.commit()
                cached_cat.reset()
                msg = gettext("Category added")
                flash(msg, 'success')
            else:
                flash(gettext('Please correct the errors'), 'error')
        categories = cached_cat.get_all()
        n_apps_per_category = dict()
        for c in categories:
            n_apps_per_category[c.short_name] = cached_apps.n_count(c.short_name)

        return render_template('admin/categories.html',
                               title=gettext('Categories'),
                               categories=categories,
                               n_apps_per_category=n_apps_per_category,
                               form=form)
    except HTTPException:
        return abort(403)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/categories/del/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def del_category(id):
    """Deletes a category"""
    try:
        category = db.session.query(model.Category).get(id)
        if category:
            if len(cached_cat.get_all()) > 1:
                require.category.delete(category)
                if request.method == 'GET':
                    return render_template('admin/del_category.html',
                                           title=gettext('Delete Category'),
                                           category=category)
                if request.method == 'POST':
                    db.session.delete(category)
                    db.session.commit()
                    msg = gettext("Category deleted")
                    flash(msg, 'success')
                    cached_cat.reset()
                    return redirect(url_for(".categories"))
            else:
                msg = gettext('Sorry, it is not possible to delete the only \
                                   available category. You can modify it, click the \
                                   edit button')
                flash(msg, 'warning')
                return redirect(url_for('.categories'))
        else:
            return abort(404)
    except HTTPException:
        return abort(403)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)


@blueprint.route('/categories/update/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_category(id):
    """Updates a category"""
    try:
        category = db.session.query(model.Category).get(id)
        if category:
            require.category.update(category)
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
                    new_category = model.Category(id=form.id.data,
                                                  name=form.name.data,
                                                  short_name=slug)
                    print new_category.id
                    db.session.merge(new_category)
                    db.session.commit()
                    cached_cat.reset()
                    msg = gettext("Category updated")
                    flash(msg, 'success')
                    return redirect(url_for(".categories"))
                else:
                    return render_template('admin/update_category.html',
                                           title=gettext('Update Category'),
                                           category=category,
                                           form=form)
        else:
            return abort(404)
    except HTTPException:
        return abort(403)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)
