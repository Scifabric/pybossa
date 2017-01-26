# -*- coding: utf8 -*-
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
"""Help view for PYBOSSA."""
from flask import Blueprint
from flask import render_template
from pybossa.util import handle_content_type
from pybossa.cache import projects as cached_projects
from pybossa.cache import categories as cached_cat
from random import choice
from readability.readability import Document

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
    cleaned_up_content = Document(render_template('help/cookies_policy.html')).summary()
    response = dict(template='help/cookies_policy.html',
                    content=cleaned_up_content,
                    title='Help: Cookies Policy')
    return handle_content_type(response)


@blueprint.route('/privacy')
def privacy():
    """Render help/privacy policy page."""
    # use readability to remove styling and headers
    cleaned_up_content = Document(render_template('help/privacy.html')).summary()
    response = dict(template='help/privacy.html',
                    content=cleaned_up_content,
                    title='Privacy Policy')
    return handle_content_type(response)
