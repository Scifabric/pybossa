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

def get_number_members(team_id):
    """Return number of Public Teams"""
    sql = text('''select count(*) from User2Team where team_id=:team_id;''')
    results = db.engine.execute(sql, team_id=team_id)
    for row in results:
        count = row[0]
 
    return count
	
def get_rank(team_id):
    ''' Score and Rank '''
    sql = text('''
               WITH  global_rank as(
               WITH scores AS( 
               SELECT team_id, count(*) AS score FROM user2team 
               INNER JOIN task_run ON user2team.user_id = task_run.user_id 
               GROUP BY user2team.team_id ) 
               SELECT team_id,score,rank() OVER (ORDER BY score DESC)  
               FROM  scores) 
               SELECT  * from global_rank where team_id=:team_id;
               ''')

    results = db.engine.execute(sql, team_id=team_id)
    rank = 0
    score = 0
    for result in results:
        rank  = result.rank
        score = result.score
		
    return rank, score
