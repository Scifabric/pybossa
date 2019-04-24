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
"""Leaderboard view for PYBOSSA."""
from flask import Blueprint, current_app, request, abort
from flask_login import current_user, login_required
from pybossa.cache import users as cached_users
from pybossa.util import handle_content_type

blueprint = Blueprint('leaderboard', __name__)


@blueprint.route('/')
@blueprint.route('/window/<int:window>')
@login_required
def index(window=0):
    """Get the last activity from users and projects."""
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = None

    if window >= 10:
        window = 10

    info = request.args.get('info')

    leaderboards = current_app.config.get('LEADERBOARDS')

    if info is not None:
        if leaderboards is None or info not in leaderboards:
            return abort(404)

    top_users = cached_users.get_leaderboard(current_app.config['LEADERBOARD'],
                                             user_id=user_id,
                                             window=window,
                                             info=info)

    response = dict(template='/stats/index.html',
                    title="Community Leaderboard",
                    top_users=top_users)
    return handle_content_type(response)
