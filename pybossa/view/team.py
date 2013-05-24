# file is part of PyBOSSA.
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

from itsdangerous import BadData
from markdown import markdown

from flask import Blueprint
from flask import render_template
from flask import request
from flask import abort
from flask import flash
from flask import redirect
from flask import url_for
from flaskext.login import login_required, current_user
from flask.ext.mail import Message
from flaskext.wtf import Form, TextField, PasswordField, validators, \
        ValidationError, IntegerField, HiddenInput, SelectField, BooleanField

from pybossa.core import db, mail
import pybossa.validator as pb_validator
import pybossa.model as model
from flaskext.babel import lazy_gettext
from sqlalchemy.sql import func, text
from pybossa.model import User, Team, User2Team
from pybossa.util import Pagination
from pybossa.auth import require
from sqlalchemy import or_, func, and_
from pybossa.cache import teams as cached_teams
from werkzeug.exceptions import HTTPException

blueprint = Blueprint('team', __name__)

def team_title(team, page_name):
    if not team:
        return "Team not found"
    if page_name is None:
        return "Team: %s" % (team.name)
    return "Team: %s &middot; %s" % (team.name, page_name)

def team_by_name(name):
    if current_user.is_anonymous():    
       return Team.query.filter_by(name=name, public='t').first_or_404()
    else:
       return Team.query.filter_by(name=name).first_or_404()

def team_current(name):
   ''' Obtain the team of of de current_user '''
   if current_user.admin == 1:
       return Team.query.filter(Team.name==name)\
                        .first_or_404()
   else:
       return Team.query.filter(Team.owner==current_user.id)\
                        .filter(Team.name==name)\
                        .first_or_404()

def get_signed_teams(page=1, per_page=5):
   '''Return a list of public teams with a pagination'''

   sql = text('''
              SELECT count(*)
              FROM team 
              INNER JOIN "user" ON team.owner="user".id
              INNER JOIN user2team on team.id=user2team.team_id
              WHERE user2team.user_id=:user_id
              ''')
   results = db.engine.execute(sql, user_id=current_user.id)
   for row in results:
       count = row[0]
    
   sql = text('''
              SELECT team.id,team.name,team.description,team.created,
              team.owner,"user".name as owner_name
              FROM team 
              INNER JOIN "user" ON team.owner="user".id
              INNER JOIN user2team on team.id=user2team.team_id
              WHERE user2team.user_id=:user_id
              OFFSET(:offset) LIMIT(:limit);
              ''')

   offset = (page - 1) * per_page
   results = db.engine.execute(sql, user_id=current_user.id, limit=per_page, offset=offset)
   teams = []
   for row in results:
       team = dict(id=row.id, name=row.name,
                   created=row.created, description=row.description,
                   owner=row.owner,
                   owner_name=row.owner_name
                   )
    
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

       results = db.engine.execute(sql, team_id=row.id)
       for result in results:
           team['rank'] = result.rank
           team['score'] = result.score

       teams.append(team)

   return teams, count

# Ok
class TeamForm(Form):
   ''' Modify Team '''
   id = IntegerField(label=None, widget=HiddenInput())
   err_msg = lazy_gettext("Team Name must be between 3 and 35 characters long")
   err_msg_2 = lazy_gettext("The team name is already taken")
   name = TextField(lazy_gettext('Team Name'),
                         [validators.Length(min=3, max=35, message=err_msg),
                          pb_validator.Unique(db.session, Team,
                                              Team.name, err_msg_2)])

   err_msg = lazy_gettext("Team Description must be between 3 and 35 characters long")
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=35, message=err_msg)])

   public = BooleanField(lazy_gettext('Public'))

# Ok
@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    """By default show the Public Teams"""

    return team_index(page, cached_teams.get_publics, 'public',
                      True, False, lazy_gettext('Public Teams'))

@blueprint.route('/signed/', defaults={'page': 1})
@blueprint.route('/signed/page/<int:page>')
@login_required
def signed(page):
    """By show the Signed Teams"""

    #if current_user.is_anonymous():    
    #   list_teams = cached_teams.get_publics
    #else:

    list_teams = get_signed_teams

    return team_index(page, list_teams, 'signed',
                      True, False, lazy_gettext('Signed Teams'))
# Ok
def team_index(page, lookup, team_type, fallback, use_count, title):
    """Show apps of app_type"""
    if not require.team.read():
        abort(403)
  
    per_page = 5

    teams, count = lookup(page, per_page)

    team_owner = []
    if not current_user.is_anonymous():
       team_owner = Team.query.filter(Team.owner==current_user.id).first()
   
       for team in teams:
           user2team = User2Team.query.filter(User2Team.team_id==team['id'])\
                                        .filter(User2Team.user_id==current_user.id)\
                                        .first()
           team['belong'] = (1, 0)[user2team is None]
    
    #if fallback and not apps:
    #    return redirect(url_for('.published'))

    pagination = Pagination(page, per_page, count)
    template_args = {
        "teams": teams,
        "team_owner": team_owner,
        "title": title,
        "pagination": pagination,
        "team_type": team_type}

    if use_count:
        template_args.update({"count": count})

    return render_template('/team/index.html', **template_args)

# Ok
@blueprint.route('/<name>/')
def details(name=None):
   team = team_by_name(name)

   try:
       require.team.read(team)
       #require.team.update(team)
       template = '/team/team.html'
   except HTTPException:
       #if team.hidden:
       #    team = None
       print "exception"
       template = '/team/index.html'

   title = team_title(team, None)
   template_args = {"team": team, "title": title}

   return render_template(template, **template_args)

# Ok
@blueprint.route('/<name>/settings')
@login_required
def settings(name):
   team = team_by_name(name)

   title = team_title(team, "Settings")
   try:
       require.team.read(team)
       require.team.update(team)

       return render_template('/team/settings.html',
                               team=team,
                               title=title)
   except HTTPException:
       return abort(403)

@blueprint.route('/<type>/search', methods=['GET', 'POST'])
def search_teams(type):

   form = SearchForm(request.form)
   teams = db.session.query(Team)\
                .all()

   if request.method == 'POST' and form.user.data:
       query = '%' + form.user.data.lower() + '%'

       print type
       if type == 'public':
           founds = db.session.query(Team)\
                      .filter(func.lower(Team.name).like(query))\
                      .filter(Team.public=='t')\
                      .all()
       else:
           founds = db.session.query(Team)\
                      .join(User2Team)\
                      .filter(func.lower(Team.name).like(query))\
                      .filter(User2Team.user_id == current_user.id)\
                      .all()
       if not founds:
           flash("<strong>Ooops!</strong> We didn't find a team "
                  "matching your query: <strong>%s</strong>" % form.user.data)

           return render_template('/team/search_teams.html', 
                          founds= [],
                          team_type = type,
                          title=lazy_gettext('Search Team'))
       else:
           return render_template('/team/search_teams.html', 
                          founds= founds,
                          team_type = type,
                          title=lazy_gettext('Search Team'))

   return render_template('/team/search_teams.html', 
                          found=[],
                          team_type = type,
                          title=lazy_gettext('Search Team'))

@blueprint.route('/<name>/users/search', methods=['GET', 'POST'])
@login_required
def search_users(name):

   team = team_current(name)

   form = SearchForm(request.form)
   users = db.session.query(User)\
                .all()

   if request.method == 'POST' and form.user.data:
       query = '%' + form.user.data.lower() + '%'
       founds = db.session.query(User)\
                  .filter(or_(func.lower(User.name).like(query),
                              func.lower(User.fullname).like(query)))\
                  .all()

       if not founds:
           flash("<strong>Ooops!</strong> We didn't find a user "
                  "matching your query: <strong>%s</strong>" % form.user.data)

           return render_template('/team/search_users.html', 
                          founds=[],
                          team=team,
                          title=lazy_gettext('Search User'))
       else:
           for found in founds:
               user2team = User2Team.query.filter(User2Team.team_id==team.id)\
                                                .filter(User2Team.user_id==found.id)\
                                                .first()
               found.belong = (1, 0)[user2team is None]

           return render_template('/team/search_users.html',
                            founds =founds,
                            team = team,
                            title=lazy_gettext('Search User'))

   return render_template('/team/search_users.html', 
                          founds=[],
                          team=team,
                          title=lazy_gettext('Search User'))

class SearchForm(Form):
   user = TextField(lazy_gettext('User'))

@blueprint.route('/new/', methods=['GET', 'POST'])
@login_required
def new():
   team = Team.query.filter(Team.owner==current_user.id).first()
   if team:
       flash("<strong>Ooops!</strong> You already ownn your group "
           "<strong>%s</strong>" % team.name)
       return redirect(url_for('team.index'))

   form = TeamForm(request.form)

   def respond(errors):
       return render_template('team/new.html',
                               title=lazy_gettext("Create a Team"),
                               form=form, errors=errors)

   if request.method != 'POST':
       return respond(False)

   if not form.validate():
       flash(lazy_gettext('Please correct the errors'), 'error')
       return respond(True)

        
   team = Team( name=form.name.data,
                       description=form.description.data,
                       public=form.public.data,
                       owner=current_user.id)

   cached_teams.reset()
   db.session.add(team)
   db.session.commit()

   # Insert into the current user in the new group 
   user2team = User2Team( user_id = current_user.id,
                                 team_id = team.id)

   db.session.add(user2team)
   db.session.commit()
        
   flash(lazy_gettext('Team created'), 'success')
   return redirect(url_for('.details', name=team.name))

@blueprint.route('/<name>/settings')
@login_required
def settings(name):
   team = team_by_name(name)

   title = team_title(team, "Settings")
   try:
       require.team.read(team)
       require.team.update(team)

       return render_template('/team/settings.html',
                               team=team,
                               title=title)
   except HTTPException:
       return abort(403)


@blueprint.route('/<name>/users')
def users(name):
   team = team_by_name(name)

   # Search users in the team
   belongs = User2Team.query.filter(User2Team.team_id == team.id)\
                                  .all()

   template = '/team/users.html'
   title = team_title(team, None)
   template_args = {
                    "team": team, 
                    "belongs": belongs,
                    "title": title}

   return render_template(template, **template_args)

# OK
@blueprint.route('/<name>/delete', methods=['GET', 'POST'])
@login_required
def delete(name):
   ''' Delete the team owner of de current_user '''
   team = team_current(name)
   title = team_title(team, "Delete")

   if not require.team.delete(team):
      abort(403)

   if request.method == 'GET':
       return render_template('/team/delete.html',
                               title=title,
                               team=team)
   
   cached_teams.clean(team.id)
   db.session.delete(team)
   db.session.commit()

   flash(lazy_gettext('Team deleted!'), 'success')
   return redirect(url_for('team.index'))

# OK
@blueprint.route('/<name>/update', methods=['GET', 'POST'])
@login_required
def update(name):
   ''' Update the team owner of the current user '''
   team = team_current(name)
  
   def handle_valid_form(form):
       new_team = Team(id=form.id.data,
                                name=form.name.data,
                                description=form.description.data,
                                public=form.public.data)

       db.session.merge(new_team)
       db.session.commit()

       flash(lazy_gettext('Team updated!'), 'success')
       return redirect(url_for('.details',
                                name=new_team.name))

   if not require.team.update(team):
       abort(403)

   title = team_title(team, "Update")
   if request.method == 'GET':
       form = TeamForm(obj=team)
       form.populate_obj(team)

   if request.method == 'POST':
       form = TeamForm(request.form)
       if form.validate():
           return handle_valid_form(form)
       flash(lazy_gettext('Please correct the errors'), 'error')        

   return render_template('/team/update.html',
                           form=form,
                           title=title,
                           team=team)

'''
@blueprint.route('/add', methods=['GET', 'POST'])
@login_required
   #    abort(403)

   # If exists goes to details  
   #team = model.Team.query.filter(Team.owner==current_user.id).first()
   #if team:
   #    template = '/team/index.html'
   #    title = team_title(team, None)
   #    template_args = {"team": team, "title": title}
   #    return render_template(template, **template_args)

   form = TeamForm(request.form)

   def respond(errors):
       return render_template('team/new.html',
                               title=lazy_gettext("Create a Team"),
                               form=form, errors=errors)

   if request.method != 'POST':
       return respond(False)

   if not form.validate():
       flash(lazy_gettext('Please correct the errors'), 'error')
       return respond(True)

        
   team = model.Team( name=form.name.data,
                       description=form.description.data,
                       public=form.public.data,
                       owner=current_user.id)

   cached_teams.reset()
   db.session.add(team)
   # mirar si lo podemos quitar
   db.session.commit()

   # Insert into the current user in the new group 
   user2team = model.User2Team( user_id = current_user.id,
                                 team_id = team.id)

   db.session.add(user2team)
   db.session.commit()
        
   flash(lazy_gettext('Team created'), 'success')
   return redirect(url_for('.details', name=team.name))

   #if request.method == 'POST' and not form.validate():
'''

@blueprint.route('/<name>/settings')
@login_required
def settings(name):
   team = team_by_name(name)

   title = team_title(team, "Settings")
   try:
       require.team.read(team)
       require.team.update(team)

       return render_template('/team/settings.html',
                               team=team,
                               title=title)
   except HTTPException:
       return abort(403)

# Ok
@blueprint.route('/<name>/delete', methods=['GET', 'POST'])
@login_required
def delete(name):
   ''' Delete the team owner of de current_user '''
   team = team_current(name)
   title = team_title(team, "Delete")

   if not require.team.delete(team):
      abort(403)

   if request.method == 'GET':
       return render_template('/team/delete.html',
                               title=title,
                               team=team)
   
   cached_teams.clean(team.id)
   db.session.delete(team)
   db.session.commit()

   flash(lazy_gettext('Team deleted!'), 'success')
   return redirect(url_for('team.index'))

# OK
@blueprint.route('/<name>/update', methods=['GET', 'POST'])
@login_required
def update(name):
   ''' Update the team owner of the current user '''
   team = team_current(name)
  
   def handle_valid_form(form):
       new_team = Team(id=form.id.data,
                                name=form.name.data,
                                description=form.description.data,
                                public=form.public.data)

       db.session.merge(new_team)
       db.session.commit()

       flash(lazy_gettext('Team updated!'), 'success')
       return redirect(url_for('.details',
                                name=new_team.name))

   if not require.team.update(team):
       abort(403)

   title = team_title(team, "Update")
   if request.method == 'GET':
       form = TeamForm(obj=team)
       form.populate_obj(team)

   if request.method == 'POST':
       form = TeamForm(request.form)
       if form.validate():
           return handle_valid_form(form)
       flash(lazy_gettext('Please correct the errors'), 'error')        

   return render_template('/team/update.html',
                           form=form,
                           title=title,
                           team=team)

@blueprint.route('/<name>/join', methods=['GET', 'POST'])
@login_required
def user_add(name):
   ''' Add Current User to a team '''
   team = team_by_name(name)
  
   # Search relationship
   user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == current_user.id )\
                   .filter(User2Team.team_id == team.id )\
                   .first()

   if user2team:
       flash( lazy_gettext('This user already is in this team'), 'error')
       return redirect(url_for('team.search_users',  name=team.name ))

   else:
       user2team = User2Team(
                      user_id = current_user.id,
                      team_id = team.id)

       db.session.add(user2team)
       db.session.commit()
       flash( lazy_gettext('Association to the team created'), 'success')
       return redirect(url_for('team.signed' ))

@blueprint.route('/<name>/separate', methods=['GET', 'POST'])
@login_required
def user_delete(name):
   team = team_by_name(name)

   ''' Check if exits association'''
   user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == current_user.id )\
                   .filter(User2Team.team_id == team.id )\
                   .first()

   if user2team:
       db.session.delete(user2team)
       db.session.commit()
       flash(lazy_gettext('Association to the team deleted'), 'success')

   return redirect(url_for('team.signed', name=name))

@blueprint.route('/<name>/join/<user>', methods=['GET', 'POST'])
@login_required
def join_add(name,user):
   ''' Add user from a team '''
   team = team_current(name)
  
   user = User.query.filter_by(name=user).first()
   if not user:
       flash( lazy_gettext('This user don\t exists!!!'), 'error')
       return redirect(url_for('team.index',  name=team.name ))

   # Search relationship
   user2team = db.session.query(User2Team)\
                 .filter(User2Team.user_id == user.id )\
                 .filter(User2Team.team_id == team.id )\
                 .first()

   if user2team:
       flash( lazy_gettext('This user already is in this team'), 'error')
       return redirect(url_for('team.searchusers',  name=team.name ))

   else:
       user2team = User2Team(
                      user_id = user.id,
                      team_id = team.id)

       db.session.add(user2team)
       db.session.commit()
       flash( lazy_gettext('Association to the team created'), 'success')
       return redirect(url_for('team.users',  name=team.name ))

@blueprint.route('/<name>/separate/<user>', methods=['GET', 'POST'])
@login_required
def join_delete(name, user):
   ''' Delete user from a team '''
   team = team_current(name)

   user = User.query.filter_by(name=user).first()
   if not user:
       flash( lazy_gettext('This user doesn\'t exists!!!'), 'error')
       return redirect(url_for('team.index'))

   ''' Check if exits association'''
   user2team = db.session.query(User2Team)\
                  .filter(User2Team.user_id == user.id )\
                  .filter(User2Team.team_id == team.id )\
                  .first()

   if user2team:
       db.session.delete(user2team)
       db.session.commit()

       flash(lazy_gettext('The user has been deleted to the team correctly!'), 'success')

   return redirect(url_for('team.signed'))

def get_team_score(team):
   '''' Get total score by team '''
   sql = text('''
       WITH  global_rank as(
         WITH scores AS( 
         SELECT team_id, count(*) AS score FROM user2team 
         INNER JOIN task_run ON user2team.user_id = task_run.user_id 
         GROUP BY user2team.team_id ) 
         SELECT team_id,score,rank() OVER (ORDER BY score DESC)  
         FROM  scores) 
       SELECT  * from global_rank where team_id=:team_id;''')

   results = db.engine.execute(sql, team_id=team.id)
   
   for result in results:
      team.rank = result.rank
      team.score = result.score
