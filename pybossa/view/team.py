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
import pybossa.team as team_func

blueprint = Blueprint('team', __name__)

def team_title(team, page_name):
    if not team:
        return "Team not found"
    if page_name is None:
        return "Team: %s" % (team.name)
    return "Team: %s &middot; %s" % (team.name, page_name)

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

@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
   '''By default show the Public Teams'''
   return team_index(page, cached_teams.get_public_data, 'public',
                      True, False, lazy_gettext('Public Teams'))

@blueprint.route('/private/', defaults={'page': 1})
@blueprint.route('/private/page/<int:page>')
@login_required
def private(page):
   if current_user.admin != 1:
       abort(404) 

   '''By show the private Teams'''
   return team_index(page, team_func.get_private_teams, 'private',
                      True, False, lazy_gettext('Private Teams'))


@blueprint.route('/myteams', defaults={'page': 1})
@blueprint.route('/myteams/page/<int:page>')
@login_required
def myteams(page):
   if not require.team.create():
       abort(403)

   # First Get own team
   #teams = Team.query.filter(Team.owner_id==current_user.id).all()
   #teams = db.session.query(Team)\
   #                  .join(User2Team)


   '''By show the private Teams'''
   return team_index(page, team_func.get_signed_teams, 'myteams',
                      True, False, lazy_gettext('My Teams'))

'''
   teams = Team.query.outerjoin(User2Team)\
                     .filter(or_ (Team.owner_id ==current_user.id, User2Team.user_id == current_user.id))\
                     .all()

   return render_template('team/myteams.html',
                          title=lazy_gettext("My Teams"),
                          teams = teams)
'''
					  
def team_index(page, lookup, team_type, fallback, use_count, title):
   '''Show apps of app_type'''
   if not require.team.read():
       abort(403)
  
   per_page = 5

   teams, count = lookup(page, per_page)

   team_owner = []
   if not current_user.is_anonymous():
       team_owner = Team.query.filter(Team.owner_id==current_user.id).first()
   
       for team in teams:
           team['belong'] = team_func.user_belong_team(team['id'])
    
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

@blueprint.route('/<name>/')
def detail(name=None):
   ''' Team details '''
   if not require.team.read():
        abort(403)

   team = team_func.get_team(name)
   title = team_title(team, team.name)
   
   # Get extra data 
   data = dict( belong = team_func.user_belong_team(team.id),
                members = team_func.get_number_members(team.id))
   data['rank'], data['score'] = team_func.get_rank(team.id)
   
   try:
       require.team.read(team)
       template = '/team/team.html'
   except HTTPException:
       template = '/team/index.html'

   template_args = {
                    "team": team, 
		    "title": title,
		    "data": data,
                   }

   return render_template(template, **template_args)

@blueprint.route('/<name>/settings')
@login_required
def settings(name):
   team = team_func.get_team(name)
   title = lazy_gettext('Settings')

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
   ''' Search Teams '''
   if not require.team.read():
        abort(403)

   title = lazy_gettext('Search name of teams')
   form = SearchForm(request.form)
   teams = db.session.query(Team)\
                     .all()

   if request.method == 'POST' and form.user.data:
       query = '%' + form.user.data.lower() + '%'

       if type == 'public':
           founds = db.session.query(Team)\
                      .filter(func.lower(Team.name).like(query))\
                      .filter(Team.public == True)\
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
   ''' Search users in a team'''
   if not require.team.read():
        abort(403)

   team = team_func.get_team(name)

   form = SearchForm(request.form)
   users = db.session.query(User).all()

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
                          title=lazy_gettext('Search name of User'))
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
   if not require.team.create():
       abort(403)

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
                       owner_id=current_user.id)
   try:
       cached_teams.reset()
       db.session.add(team)
       db.session.commit()

       # Insert into the current user in the new group 
       user2team = User2Team( user_id = current_user.id,
                          team_id = team.id)

       db.session.add(user2team)
       db.session.commit()
        
       flash(lazy_gettext('Team created'), 'success')
       return redirect(url_for('.detail', name=team.name))
   except Exception as e:
       flash( e ,'error')
       return redirect(url_for('.myteams'))

@blueprint.route('/<name>/users')
def users(name):
   team = team_func.get_team(name)
   title = lazy_gettext('Search Users')

   if not require.team.read():
       abort(403)

   # Search users in the team
   belongs = User2Team.query.filter(User2Team.team_id == team.id)\
                                  .all()

   template = '/team/users.html'
   template_args = {
                    "team": team, 
                    "belongs": belongs,
                    "title": title}

   return render_template(template, **template_args)

@blueprint.route('/<name>/delete', methods=['GET', 'POST'])
@login_required
def delete(name):
   ''' Delete the team owner of de current_user '''
   team = team_func.get_team(name)
   title = lazy_gettext('Delete Team')

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
   return redirect(url_for('team.myteams'))

@blueprint.route('/<name>/update', methods=['GET', 'POST'])
@login_required
def update(name):
   ''' Update the team owner of the current user '''
   team = team_func.get_team(name)
   title = lazy_gettext('Update Team')

   if not require.team.update(team):
       abort(403)
  
   def handle_valid_form(form):
       new_team = Team(id=form.id.data,
                                name=form.name.data,
                                description=form.description.data,
                                public=form.public.data)

       db.session.merge(new_team)
       db.session.commit()

       flash(lazy_gettext('Team updated!'), 'success')
       return redirect(url_for('.detail',
                                name=new_team.name))

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
   team = team_func.get_team(name)
   title = lazy_gettext('Add User to a Team')

   if not require.team.read():
       abort(403)
  
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
       return redirect(url_for('team.myteams' ))

@blueprint.route('/<name>/separate', methods=['GET', 'POST'])
@login_required
def user_delete(name):
   team = team_func.get_team(name)
   title = lazy_gettext('Delete User from a Team')

   if not require.team.read():
       abort(403)

   ''' Check if exits association'''
   user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == current_user.id )\
                   .filter(User2Team.team_id == team.id )\
                   .first()

   if user2team:
       db.session.delete(user2team)
       db.session.commit()
       flash(lazy_gettext('Association to the team deleted'), 'success')

   return redirect(url_for('team.myteams'))

@blueprint.route('/<name>/join/<user>', methods=['GET', 'POST'])
@login_required
def join_add(name,user):
   ''' Add user from a team '''
   team = team_func.get_team(name)
   title = lazy_gettext('Create association')

   if not require.team.update(team):
       abort(403)
  
   user = User.query.filter_by(name=user).first()
   if not user:
       flash( lazy_gettext('This user don\t exists!!!'), 'error')
       return redirect(url_for('team.myteams',  name=team.name ))

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
   team = team_func.get_team(name)
   title = lazy_gettext('Delete association')

   if not require.team.update(team):
      abort(403)

   user = User.query.filter_by(name=user).first()
   if not user:
       flash( lazy_gettext('This user doesn\'t exists!!!'), 'error')
       return redirect(url_for('team.myteams'))

   ''' Check if exits association'''
   user2team = db.session.query(User2Team)\
                  .filter(User2Team.user_id == user.id )\
                  .filter(User2Team.team_id == team.id )\
                  .first()

   if user2team:
       db.session.delete(user2team)
       db.session.commit()

       flash(lazy_gettext('The user has been deleted to the team correctly!'), 'success')

   return redirect(url_for('team.myteams'))
