# -*- coding: utf8 -*-
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
"""Home view for PyBossa."""
from flask import current_app, abort
from flask.ext.login import current_user
from pybossa.model.category import Category
from flask import Blueprint
from flask import render_template
from pybossa.cache import projects as cached_projects
from pybossa.cache import users as cached_users
from pybossa.cache import categories as cached_cat
from pybossa.util import rank
from jinja2.exceptions import TemplateNotFound


blueprint = Blueprint('home', __name__)


@blueprint.route('/')
def home():
    """Render home page with the cached projects and users."""
    page = 1
    per_page = current_app.config.get('APPS_PER_PAGE')
    if per_page is None:  # pragma: no cover
        per_page = 5
    d = {'top_projects': cached_projects.get_top(),
         'top_users': None}

    # Get all the categories with projects
    categories = cached_cat.get_used()
    d['categories'] = categories
    d['categories_projects'] = {}
    for c in categories:
        tmp_projects = cached_projects.get(c['short_name'], page, per_page)
        d['categories_projects'][c['short_name']] = rank(tmp_projects)

    # Add featured
    tmp_projects = cached_projects.get_featured('featured', page, per_page)
    if len(tmp_projects) > 0:
        featured = Category(name='Featured', short_name='featured')
        d['categories'].insert(0, featured)
        d['categories_projects']['featured'] = rank(tmp_projects)

    if (current_app.config['ENFORCE_PRIVACY']
            and current_user.is_authenticated()):
        if current_user.admin:
            d['top_users'] = cached_users.get_leaderboard(10)
    if not current_app.config['ENFORCE_PRIVACY']:
        d['top_users'] = cached_users.get_leaderboard(10)
    return render_template('/home/index.html', **d)


@blueprint.route("about")
def about():
    """Render the about template."""
    return render_template("/home/about.html")


@blueprint.route("search")
def search():
    """Render search results page."""
    return render_template("/home/search.html")

@blueprint.route("results")
def result():
    """Render a results page."""
    try:
        return render_template("/home/_results.html")
    except TemplateNotFound:
        return abort(404)
