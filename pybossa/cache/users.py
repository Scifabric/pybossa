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
from sqlalchemy.sql import func
from pybossa.core import cache
from pybossa.core import db
from pybossa.model import User, TaskRun

@cache.cached(timeout=60*5, key_prefix='top_users')
def get_top(n=10):
    """Return the n=10 top users"""
    top_active_user_ids = db.session\
            .query(TaskRun.user_id,
                    func.count(TaskRun.id).label('total'))\
            .group_by(TaskRun.user_id)\
            .order_by('total DESC')\
            .limit(n)\
            .all()
    top_users = []
    for id in top_active_user_ids:
        if id[0] is not None:
            u = db.session.query(User).get(id[0])
            tmp = dict(user=u, apps=[], task_runs=len(u.task_runs))
            top_users.append(tmp)
    return top_users
