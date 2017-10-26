# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
"""Home view for PYBOSSA."""
from flask import current_app, abort
from flask.ext.login import current_user
from pybossa.model.category import Category
from flask import Blueprint
from flask import render_template
from pybossa.cache import projects as cached_projects
from pybossa.cache import users as cached_users
from pybossa.cache import categories as cached_cat
from pybossa.util import rank, handle_content_type
from jinja2.exceptions import TemplateNotFound


blueprint = Blueprint('home', __name__)


@blueprint.route('/')
def home():
    """Render home page with the cached projects and users."""
    page = 1
    per_page = current_app.config.get('APPS_PER_PAGE', 5)

    # Add featured
    tmp_projects = cached_projects.get_featured('featured', page, per_page)
    if len(tmp_projects) > 0:
        data = dict(featured=rank(tmp_projects))
    else:
        data = dict(featured=[])
    response = dict(template='/home/index.html', **data)
    return handle_content_type(response)


@blueprint.route("about")
def about():
    """Render the about template."""
    response = dict(template="/home/about.html")
    return handle_content_type(response)


@blueprint.route("search")
def search():
    """Render search results page."""
    response = dict(template="/home/search.html")
    return handle_content_type(response)

@blueprint.route("results")
def result():
    """Render a results page."""
    try:
        response = dict(template="/home/_results.html")
        return handle_content_type(response)
    except TemplateNotFound:
        return abort(404)
