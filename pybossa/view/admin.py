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
from flaskext.login import login_required, current_user
from flaskext.wtf import Form, TextField, IntegerField, HiddenInput, validators
from flaskext.babel import lazy_gettext

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
    n_published = cached_apps.n_published()
    if request.method == 'GET':
        apps, n_published = cached_apps.get_published(page=1, per_page=n_published)
        return render_template('/admin/applications.html', apps=apps)
    if request.method == 'POST':
        cached_apps.reset()
        f = model.Featured()
        f.app_id = app_id
        # Check if the app is already in this table
        tmp = db.session.query(model.Featured)\
                .filter(model.Featured.app_id == app_id)\
                .first()
        if (tmp is None):
            db.session.add(f)
            db.session.commit()
            return json.dumps(f.dictize())
        else:
            return json.dumps({'error': 'App.id %s already in Featured table'
                               % app_id})
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
            return json.dumps({'error': 'App.id %s is not in Featured table'
                               % app_id})


class SearchForm(Form):
    user = TextField(lazy_gettext('User'))


@blueprint.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users(user_id=None):
    """Manage users of PyBossa"""
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
        if not found:
            flash("<strong>Ooops!</strong> We didn't find a user "
                  "matching your query: <strong>%s</strong>" % form.user.data)
        return render_template('/admin/users.html', found=found, users=users,
                               title=lazy_gettext("Manage Admin Users"), form=form)

    return render_template('/admin/users.html', found=[], users=users,
                           title=lazy_gettext("Manage Admin Users"), form=form)


@blueprint.route('/users/add/<int:user_id>')
@login_required
@admin_required
def add_admin(user_id=None):
    """Add admin flag for user_id"""
    if user_id:
        user = db.session.query(model.User)\
                 .get(user_id)
        if user:
            user.admin = True
            db.session.commit()
            return redirect(url_for(".users"))
        else:
            return abort(404)


@blueprint.route('/users/del/<int:user_id>')
@login_required
@admin_required
def del_admin(user_id=None):
    """Del admin flag for user_id"""
    if user_id:
        user = db.session.query(model.User)\
                 .get(user_id)
        if user:
            user.admin = False
            db.session.commit()
            return redirect(url_for('.users'))
        else:
            return abort(404)
    else:
        return abort(404)


class CategoryForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(db.session, model.Category, model.Category.name,
                                          message="Name is already taken.")])


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
                                          short_name=slug)
                db.session.add(category)
                db.session.commit()
                cached_cat.reset()
                msg = lazy_gettext("Category added")
                flash(msg, 'success')
            else:
                flash(lazy_gettext('Please correct the errors'), 'error')
        categories = cached_cat.get()
        return render_template('admin/categories.html',
                               title=lazy_gettext('Categories'),
                               categories=categories,
                               form=form)
    except:
        raise
        return abort(403)


@blueprint.route('/categories/del/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def del_category(id):
    """Deletes a category"""
    try:
        category = db.session.query(model.Category).get(id)
        if category:
            require.category.delete(category)
            if request.method == 'GET':
                return render_template('admin/del_category.html',
                                       title=lazy_gettext('Delete Category'),
                                       category=category)
            if request.method == 'POST':
                db.session.delete(category)
                db.session.commit()
                msg = lazy_gettext("Category deleted")
                flash(msg, 'success')
                cached_cat.reset()
                return redirect(url_for(".categories"))
        else:
            return abort(404)
    except:
        abort(403)


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
                                       title=lazy_gettext('Update Category'),
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
                    msg = lazy_gettext("Category updated")
                    flash(msg, 'success')
                    return redirect(url_for(".categories"))
                else:
                    return render_template('admin/update_category.html',
                                           title=lazy_gettext('Update Category'),
                                           category=category,
                                           form=form)
        else:
            return abort(404)
    except:
        raise
        abort(403)
