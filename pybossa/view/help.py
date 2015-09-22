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
"""Help view for PyBossa."""
from flask import Blueprint
from flask import render_template
from pybossa.cache import projects as cached_projects
from pybossa.cache import categories as cached_cat
from random import choice

blueprint = Blueprint('help', __name__)


@blueprint.route('/api')
def api():
    """Render help/api page."""
    categories = cached_cat.get_used()
    projects = cached_projects.get(categories[0]['short_name'])
    if len(projects) > 0:
        project_id = choice(projects)['id']
    else:  # pragma: no cover
        project_id = None
    return render_template('help/api.html', title="Help: API",
                           project_id=project_id)


@blueprint.route('/license')
def license():
    """Render help/license page."""
    return render_template('help/license.html', title='Help: Licenses')


@blueprint.route('/terms-of-use')
def tos():
    """Render help/terms-of-use page."""
    return render_template('help/tos.html', title='Help: Terms of Use')


@blueprint.route('/cookies-policy')
def cookies_policy():
    """Render help/cookies-policy page."""
    return render_template('help/cookies_policy.html',
                           title='Help: Cookies Policy')


@blueprint.route('/privacy')
def privacy():
    """Render help/privacy policy page."""
    return render_template('help/privacy.html',
                           title='Help: Cookies Policy')
