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
from pybossa.cache import apps as cached_apps
from random import choice

blueprint = Blueprint('help', __name__)


@blueprint.route('/api')
def api():
    """Render help/api page"""
    apps, count = cached_apps.get_published()
    if len(apps) > 0:
        app_id = choice(apps)['id']
    else:
        app_id = None
    return render_template('help/api.html', title="Help: API",
                           app_id=app_id)


@blueprint.route('/license')
def license():
    """Render help/license page"""
    return render_template('help/license.html', title='Help: Licenses')


@blueprint.route('/terms-of-use')
def tos():
    """Render help/terms-of-use page"""
    return render_template('help/tos.html', title='Help: Terms of Use')
