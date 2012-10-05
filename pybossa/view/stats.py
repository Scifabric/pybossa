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

from flask import Blueprint, request, url_for, flash, redirect, abort
from flask import render_template
from flaskext.wtf import Form, IntegerField, TextField, BooleanField, validators, HiddenInput
from flaskext.login import login_required, current_user
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy import func

import pybossa.model as model
from pybossa.core import db
from pybossa.auth import require

blueprint = Blueprint('stats', __name__)


@blueprint.route('/')
def index():
    """Get the last activity from users and apps"""
    # Get top 5 app ids
    top5_active_app_ids = db.session\
            .query(model.TaskRun.app_id,
                    func.count(model.TaskRun.id).label('total'))\
            .group_by(model.TaskRun.app_id)\
            .order_by('total DESC')\
            .limit(5)\
            .all()
    apps = []
    # print top5_active_app_ids
    for id in top5_active_app_ids:
        if id[0] is not None:
            app = db.session.query(model.App)\
                    .get(id[0])
            if not app.hidden:
                apps.append(app)

    # Get top 5 user ids
    top5_active_user_ids = db.session\
            .query(model.TaskRun.user_id,
                    func.count(model.TaskRun.id).label('total'))\
            .group_by(model.TaskRun.user_id)\
            .order_by('total DESC')\
            .limit(5)\
            .all()
    top5Users = []
    for id in top5_active_user_ids:
        if id[0] is not None:
            u = db.session.query(model.User).get(id[0])
            # userApps =  db.session.query(model.App).join(db.TaskRun)\
            #                               .filter(model.TaskRun.user_id == u.id)
            #                               .all()

            tmp = dict(user=u, apps=[])

            top5Users.append(tmp)

    return render_template('/stats/index.html', title="Leaderboard",
            apps=apps, top5Users=top5Users)
