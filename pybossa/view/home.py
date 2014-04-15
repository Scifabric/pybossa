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

from flask import current_app
from flask.ext.login import current_user
import pybossa.model as model
from pybossa.cache import apps as cached_apps
from pybossa.cache import users as cached_users
from pybossa.cache import categories as cached_cat
from flask import Blueprint
from flask import render_template
from pybossa.cache import apps as cached_apps
from pybossa.cache import categories as cached_cat

blueprint = Blueprint('home', __name__)

@blueprint.route('/')

def home():
    """ Render home page with the cached apps and users"""
    d = {'featured': cached_apps.get_featured_front_page(),
         'top_apps': cached_apps.get_top(),
         'top_users': None}

    # Get all the categories with apps
    categories = cached_cat.get_used()
    d['categories'] = categories
    d['categories_apps'] = {}
    for c in categories:
        tmp_apps, count = cached_apps.get(c['short_name'], per_page=20)
        d['categories_apps'][str(c['short_name'])] = tmp_apps

    # Add featured
    tmp_apps, count = cached_apps.get_featured('featured', per_page=20)
    if count > 0:
        featured = model.category.Category(name='Featured', short_name='featured')
        d['categories'].insert(0,featured)
        d['categories_apps']['featured'] = tmp_apps

    if current_app.config['ENFORCE_PRIVACY'] and current_user.is_authenticated():
        if current_user.admin:
            d['top_users'] = cached_users.get_top()
    if not current_app.config['ENFORCE_PRIVACY']:
        d['top_users'] = cached_users.get_top()
    return render_template('/home/index.html', **d)


@blueprint.route("/about")
def about():
    """Render the about template"""
    return render_template("/home/about.html")

@blueprint.route("/search")
def search():
    """Render search results page"""
    return render_template("/home/search.html")
