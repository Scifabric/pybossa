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
from flask.ext.login import current_user
from pybossa.model import User, Team, User2Team
from sqlalchemy import or_, func, and_

STATS_TIMEOUT=50

@cache.cached(key_prefix="teams_get_public_count")
def get_public_count():
    ''' Return number of Public Teams '''
    sql = text('''select count(*) from team where public;''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]
    return count

@cache.cached(key_prefix="teams_get_count")
def get_count():
    ''' Return number of Teams '''
    sql = text('''select count(*) from team;''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]
    return count

@cache.cached(key_prefix="teams_get_public_data")
def get_public_data(page=1, per_page=5):
    ''' Return a list of public teams with a pagination '''
    count = get_public_count()
    sql = text('''
               SELECT team.id,team.name,team.description,team.created,
               team.owner_id,"user".name as owner, team.public
               FROM team
               INNER JOIN "user" ON team.owner_id="user".id
               WHERE public
               OFFSET(:offset) LIMIT(:limit);
               ''')

    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    teams = []
    for row in results:
        team = dict(
            id=row.id,
            name=row.name,
            created=row.created,
            description=row.description,
            owner_id=row.owner_id,
            owner=row.owner,
			public=row.public
            )

        team['rank'], team['score'] = get_rank(row.id)
        team['members'] = get_number_members(row.id)
        team['total'] = get_count()
        teams.append(team)

    return teams, count

@cache.cached(key_prefix="teams_get_summary")
@cache.memoize(timeout=50)
def get_team_summary(name):
    ''' Get TEAM data '''
    sql = text('''
            SELECT team.id,team.name,team.description,team.created,
            team.owner_id,"user".name as owner, team.public
            FROM team
            INNER JOIN "user" ON team.owner_id="user".id
            WHERE team.name=:name
            ''')

    results = db.engine.execute(sql, name=name)
    team = dict()
    for row in results:
        team = dict(
            id=row.id,
            name=row.name,
            description=row.description,
            owner=row.owner,
            public=row.public,
            created=row.created
            )

        team['rank'], team['score'] = get_rank(row.id)
        team['members'] = get_number_members(row.id)
        team['total'] = get_count()
        return team
    else:
        return None


@cache.memoize(timeout=60*5)
def get_number_members(team_id):
    ''' Return number of Public Teams '''
    sql = text('''select count(*) from User2Team where team_id=:team_id;''')
    results = db.engine.execute(sql, team_id=team_id)
    for row in results:
        count = row[0]
    return count

@cache.memoize(timeout=60*5)
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
    if results:
        for result in results:
            rank  = result.rank
            score = result.score

	return rank, score

@cache.memoize(timeout=50)
def get_team(name):
    ''' Get Team by name and owner '''
    if current_user.is_anonymous():
        return Team.query.filter_by(name=name, public=True).first_or_404()
    elif current_user.admin == 1:
       return Team.query.filter_by(name=name).first_or_404()
    else:
        return Team.query.filter(Team.name==name)\
                    .outerjoin(User2Team)\
                    .filter(or_ (Team.public ==True,\
                    User2Team.user_id == current_user.id))\
                    .first_or_404()


@cache.memoize(timeout=50)
def user_belong_team(team_id):
    ''' Is a user belong to a team'''
    if  current_user.is_anonymous():
       return 0
    else:
        belong = User2Team.query.filter(User2Team.team_id==team_id)\
                                .filter(User2Team.user_id==current_user.id)\
                                .first()
        return (1,0)[belong is None]

@cache.memoize(timeout=50)
def get_signed_teams(page=1, per_page=5):
    '''Return a list of public teams with a pagination'''
    sql = text('''
              SELECT count(*)
              FROM User2Team
              WHERE User2Team.user_id=:user_id;
              ''')

    results = db.engine.execute(sql, user_id=current_user.id)
    for row in results:
        count = row[0]

    sql = text('''
              SELECT team.id,team.name,team.description,team.created,
              team.owner_id,"user".name as owner, team.public
              FROM team
              JOIN user2team ON team.id=user2team.team_id
              JOIN "user" ON team.owner_id="user".id
              WHERE user2team.user_id=:user_id
              OFFSET(:offset) LIMIT(:limit);
              ''')

    offset = (page - 1) * per_page
    results = db.engine.execute(
            sql, limit=per_page, offset=offset, user_id=current_user.id)

    teams = []
    for row in results:
        team = dict(
                id=row.id,
                name=row.name,
                created=row.created,
                description=row.description,
                owner_id=row.owner_id,
                owner=row.owner,
                public=row.public
                )

        team['rank'], team['score'] = get_rank(row.id)
        team['members'] =get_number_members(row.id)
        teams.append(team)

    return teams, count

@cache.memoize(timeout=50)
def get_private_teams(page=1, per_page=5):
    '''Return a list of public teams with a pagination'''
    sql = text('''
              SELECT count(*)
              FROM team
              WHERE not public;
              ''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]
    sql = text('''
              SELECT team.id,team.name,team.description,team.created,
              team.owner_id,"user".name as owner, team.public
              FROM team
              INNER JOIN "user" ON team.owner_id="user".id
              WHERE not team.public
              OFFSET(:offset) LIMIT(:limit);
              ''')

    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    teams = []
    for row in results:
        team = dict(
                id=row.id,
                name=row.name,
                created=row.created,
                description=row.description,
                owner_id=row.owner_id,
                owner=row.owner,
                public=row.public
                )

        team['rank'], team['score'] = get_rank(row.id)
        team['members'] =get_number_members(row.id)
        teams.append(team)

    return teams, count

def reset():
    ''' Clean thie cache '''
    cache.delete('teams_get_public_count')
    cache.delete('teams_get_count')
    cache.delete('teams_get_public_data')
    cache.delete('teams_get_summary')
    cache.delete_memoized(get_number_members)
    cache.delete_memoized(get_rank)
    cache.delete_memoized(get_team)
    cache.delete_memoized(user_belong_team)
    cache.delete_memoized(get_signed_teams)
    cache.delete_memoized(get_private_teams)

def clean(team_id):
    ''' Clean all items in cache '''
    reset()
