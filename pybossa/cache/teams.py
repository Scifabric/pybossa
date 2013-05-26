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
from pybossa.model import Featured, Team
from pybossa.util import pretty_date
from pybossa.team import get_number_members, get_rank

import json
import string
import operator
import datetime
import time
from datetime import timedelta

STATS_TIMEOUT=50

@cache.cached(key_prefix="number_public_teams")
def n_public():
    """Return number of Public Teams"""
    sql = text('''select count(*) from team where public='t';''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]
    return count
	

def get_publics(page=1, per_page=5):
   '''Return a list of public teams with a pagination'''
   count = n_public()

   sql = text('''
               SELECT team.id,team.name,team.description,team.created,
               team.owner_id,"user".name as owner, team.public
               FROM team 
               INNER JOIN "user" ON team.owner_id="user".id
               WHERE public='t' 
               OFFSET(:offset) LIMIT(:limit);
               ''')

   offset = (page - 1) * per_page
   results = db.engine.execute(sql, limit=per_page, offset=offset)
   teams = []
   for row in results:
       team = dict(id=row.id, name=row.name,
                   created=row.created, description=row.description,
                   owner_id=row.owner_id,
                   owner=row.owner,
				   public=row.public
                   )       
		  
       team['rank'], team['score'] = get_rank(row.id)		  
       team['members'] = get_number_members(row.id)
       teams.append(team)

   return teams, count

def reset():
   """Clean thie cache"""
   cache.delete('number_public_teams')
   cache.delete_memoized(get_publics)

def reset():
   """Clean thie cache"""
   cache.delete('number_public_teams')
   cache.delete_memoized(get_publics)

def clean(team_id):
   """Clean all items in cache"""
   reset()
