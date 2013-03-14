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
from sqlalchemy.sql import func, text
from pybossa.core import cache
from pybossa.core import db
from pybossa.model import User, TaskRun

@cache.cached(key_prefix="front_page_top_users")
def get_top(n=10):
    """Return the n=10 top users"""
    sql = text('''
    SELECT t.id, "user".fullname, "user".email_addr, 
      "user".created, t.task_runs 
    FROM (
      SELECT "user".id, COUNT(task_run.id) AS task_runs 
      FROM task_run 
      LEFT JOIN "user" ON "user".id = task_run.user_id 
      GROUP BY "user".id ORDER BY task_runs LIMIT :limit) as t 
    LEFT JOIN "user" USING (id)''')

    results = db.engine.execute(sql, limit=n)
    top_users = []
    for row in results:
        top_users.append(row)
    return top_users
