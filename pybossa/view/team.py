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
from sqlalchemy import or_, func


blueprint = Blueprint('team', __name__)

@blueprint.route('/')
def index():
   ''' List of teams  '''
   # Anonymous only see public teams
   if current_user.is_anonymous():
       owner = None
       belongs = None
       teams = model.Team.query.filter(Team.public=='t').all()

       return render_template('/team/teams.html',
                              title=lazy_gettext("Teams Public"),
                              teams=teams,
                              owner=[],
                              belongs=[])
   else:
       # List all Teams
       if current_user.admin == 1:
          teams = model.Team.query.all()

       # List owner Teams and public teams
       else:
           teams = model.Team.query.filter((Team.owner==current_user.id) | (Team.public=='t')).all()

       # To know if is a owner team
       owner = model.Team.query.filter(Team.owner==current_user.id).first()
       
       # List of teams belong to
       belongs = model.User2Team.query.filter(User2Team.user_id == current_user.id)  \
                                       .all() 
   
       return render_template('/team/teams.html',
                              title=lazy_gettext("Manage Teams"),
                              teams=teams,
                              owner=owner,
                              belongs=belongs)

@blueprint.route('/<name>', methods=['GET', 'POST'])
def details(name=None):
   if not name:
       abort(404)
   else:
       if current_user.is_anonymous():
           team = model.Team.query.filter((Team.name==name) & \
                                          (Team.public=='t')).first()
       elif current_user.admin == 1:
           team = model.Team.query.filter(Team.name==name).first()

       else:
           team = model.Team.query.filter((Team.name==name) & \
                                          ((Team.public=='t') | (Team.owner==current_user.id)))\
                                  .first()
       if team is None:
         flash("<strong>Ooops!</strong> We don't find this team", 'error')
         return redirect(url_for('team.index'))

       else:
           return render_template('/team/index.html',
                            found=[],
                            team = team)         
class UpdateTeamForm(Form):
   ''' Modify Team '''
   id = IntegerField(label=None, widget=HiddenInput())
   err_msg = lazy_gettext("Team Name must be between 3 and 35 characters long")
   err_msg_2 = lazy_gettext("The team name is already taken")
   name = TextField(lazy_gettext('Team Name'),
                         [validators.Length(min=3, max=35, message=err_msg),
                          pb_validator.Unique(db.session, model.Team,
                                              model.Team.name, err_msg_2)])

   err_msg = lazy_gettext("Team Description must be between 3 and 35 characters long")
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=35, message=err_msg)])

   public = BooleanField(lazy_gettext('Public'))

@blueprint.route('/<name>/search', methods=['GET', 'POST'])
@login_required
def searchusers(name):
   team  = model.Team.query.filter(Team.name==name)\
                           .first()
   if not team:
       flash("<strong>Ooops!</strong> We didn't find this team", 'error')
       return redirect(url_for('team.index'))

   else:
       form = SearchForm(request.form)
       users = db.session.query(model.User)\
                .all()

       if request.method == 'POST' and form.user.data:
           query = '%' + form.user.data.lower() + '%'
           founds = db.session.query(model.User)\
                  .filter(or_(func.lower(model.User.name).like(query),
                              func.lower(model.User.fullname).like(query)))\
                  .all()

           belongs = dict()
           if not founds:
               flash("<strong>Ooops!</strong> We didn't find a user "
                  "matching your query: <strong>%s</strong>" % form.user.data)
            
           else:
               for found in founds:
                   user2team = model.User2Team.query.filter(User2Team.team_id==team.id)\
                                                .filter(User2Team.user_id==found.id)\
                                                .first()
                   belongs[found.id]= (1, 0)[user2team is None]

           return render_template('/team/searchusers.html',
                            found =founds,
                            belongs=belongs,
                            team = team,
                            title=lazy_gettext('Search User'))

       return render_template('/team/searchusers.html', 
                          found=[],
                          team=team,
                          title=lazy_gettext('Search User'))


class SearchForm(Form):
   user = TextField(lazy_gettext('User'))

@blueprint.route('/add', methods=['GET', 'POST'])
@login_required
def add():
   team = model.Team.query.filter(Team.owner==current_user.id).first()

   if team:
       flash("<strong>Ooops!</strong> You already ownn your group "
           "<strong>%s</strong>" % team.name)
       return redirect(url_for('team.index'))


   ''' Create Team '''
   # TODO:T re-enable csrf
   form = TeamForm(request.form)
   if request.method == 'POST' and form.validate():
        
       team = model.Team( name=form.name.data,
                          description=form.description.data,
                          public=form.public.data,
                          owner=current_user.id)
       db.session.add(team)
       db.session.commit()

       user2team = model.User2Team( user_id = current_user.id,
                          team_id = team.id)

       db.session.add(user2team)
       db.session.commit()
        
       flash(lazy_gettext('Team successfully created'), 'success')
       return redirect(url_for('team.index'))

   if request.method == 'POST' and not form.validate():
       flash(lazy_gettext('Please correct the errors'), 'error')
    
   return render_template('/team/register.html', form=form)

@blueprint.route('/<name>/delete', methods=['GET', 'POST'])
@login_required
def delete(name):
   ''' Delete the team owner of de current_user '''
   if current_user.admin == 1:
       current_team  = model.Team.query.filter(Team.name==name)\
                                       .first()
   else:
       current_team  = model.Team.query.filter(Team.owner==current_user.id)\
                                       .filter(Team.name==name)\
                                       .first()
   if current_team:
       db.session.delete(current_team)
       db.session.commit()

       flash(lazy_gettext('Your team has been deleted!'), 'success')
       return redirect(url_for('team.index'))
   else:
       flash(lazy_gettext('Oopps, The group that you try to delete doesn\t exists or you don\t are the owner.'), 'error')
       return redirect(url_for('team.index'))

@blueprint.route('/<name>/update', methods=['GET', 'POST'])
@login_required
def update(name):
   ''' Update the team owner of the current user '''
   if current_user.admin == 1:
       user_team  = model.Team.query.filter(Team.name==name)\
                                    .first()
   else:
       user_team  = model.Team.query.filter(Team.owner==current_user.id)\
                                    .filter(Team.name==name)\
                                    .first()
   if user_team:
       form = UpdateTeamForm(obj=user_team)
       if request.method == 'GET':
           title_msg = "Update team: %s" % user_team.name
           return render_template('team/update.html',
                               title=title_msg,
                               form=form,
                               team=user_team)
       else:
           form = UpdateTeamForm(request.form)
           if form.validate():
               new_profile = model.Team(id=form.id.data,
                                     name=form.name.data,
                                     description=form.description.data,
                                     public=form.public.data)

               db.session.merge(new_profile)
               db.session.commit()
            
               flash(lazy_gettext('Your team has been updated!'), 'success')
               return redirect(url_for('team.index'))

           else:
               flash(lazy_gettext('Please correct the errors'), 'error')
               title_msg = 'Update team: %s' % user_team.name
               return render_template('/team/update.html', form=form,
                                   title=title_msg)
   else:
       flash(lazy_gettext('Oopps, The group that you try to update doesn\t exists or you don\t are the owner.'), 'error')
       title_msg = 'Update team: '
       return redirect(url_for('team.index'))

@blueprint.route('/<name>/join', methods=['GET', 'POST'])
@login_required
def user_add(name):
   ''' Add user from a team '''
   if current_user.admin == 1:
       team  = model.Team.query.filter_by(name=name).first()
   else:
       team = model.Team.query.filter((Team.name==name) & \
                                      (Team.public=='t')).first()
   if team:
       # Search relationship
       user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == current_user.id )\
                   .filter(User2Team.team_id == team.id )\
                   .first()

       if user2team:
           flash( lazy_gettext('This user already is in this team'), 'error')
           return redirect(url_for('team.searchusers',  name=team.name ))

       else:
           user2team = model.User2Team(
                      user_id = current_user.id,
                      team_id = team.id)

           db.session.add(user2team)
           db.session.commit()
           flash( lazy_gettext('Association to the team created'), 'success')
           return redirect(url_for('team.details',  name=team.name ))

   else:
       abort(404)  

@blueprint.route('/<name>/separate', methods=['GET', 'POST'])
@login_required
def user_delete(name):
    if current_user.admin == 1:
       team  = model.Team.query.filter_by(name=name).first()
    else:
       team = model.Team.query.filter((Team.name==name) & \
                                      (Team.public=='t')).first()

    if team:
       ''' Check if exits association'''
       user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == current_user.id )\
                   .filter(User2Team.team_id == team.id )\
                   .first()

       if user2team:
          db.session.delete(user2team)
          db.session.commit()

          flash(lazy_gettext('Association to the team deleted'), 'success')

    return redirect(url_for('team.details',  name=name ))

@blueprint.route('/<name>/join/<user>', methods=['GET', 'POST'])
@login_required
def join_add(name,user):
   ''' Add user from a team '''
   if current_user.admin == 1:
       team  = model.Team.query.filter_by(name=name).first()
   else:
       team = model.Team.query.filter((Team.name==name) & \
                                      (Team.owner==current_user.id)).first()
   if team:
       user = model.User.query.filter_by(name=user).first()
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
           user2team = model.User2Team(
                      user_id = user.id,
                      team_id = team.id)

           db.session.add(user2team)
           db.session.commit()
           flash( lazy_gettext('Association to the team created'), 'success')
           return redirect(url_for('team.details',  name=team.name ))

   else:
       abort(404)  

@blueprint.route('/<name>/separate/<user>', methods=['GET', 'POST'])
@login_required
def join_delete(name, user):
    ''' Delete user from a team '''
    if current_user.admin == 1:
       team  = model.Team.query.filter_by(name=name).first()
    else:
       team = model.Team.query.filter((Team.name==name) & \
                                      (Team.owner==current_user.id)).first()

    if team:
       user = model.User.query.filter_by(name=user).first()
       if not user:
           flash( lazy_gettext('This user don\t exists!!!'), 'error')
           return redirect(url_for('team.details',  name=team.name ))

       ''' Check if exits association'''
       user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == user.id )\
                   .filter(User2Team.team_id == team.id )\
                   .first()

       if user2team:
          db.session.delete(user2team)
          db.session.commit()

          flash(lazy_gettext('The user has been deleted to the team correctly!'), 'success')

    return redirect(url_for('team.details',  name=name ))

class TeamForm(Form):
   err_msg = lazy_gettext("Team Name must be between 3 and 35 characters long")
   err_msg_2 = lazy_gettext("The team name is already taken")
   name = TextField(lazy_gettext('Team Name'),
                         [validators.Length(min=3, max=35, message=err_msg),
                          pb_validator.Unique(db.session, model.Team,
                                              model.Team.name, err_msg_2)])

   err_msg = lazy_gettext("Team Description must be between 3 and 35 characters long")
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=35, message=err_msg)])

   public = BooleanField(lazy_gettext('Public'), default=False)

class TeamUserForm(Form):
   team = SelectField(lazy_gettext('Team name'), coerce=int)
 
   def set_teams(self, teams):
       ''' Fill the teams.choices '''
       choices = []
       for team in teams:
           choices.append((team.id,team.name))
       self.team.choices = choices

''' Modify Team '''
class UpdateTeamForm(Form):
   id = IntegerField(label=None, widget=HiddenInput())
   err_msg = lazy_gettext("Team Name must be between 3 and 35 characters long")
   err_msg_2 = lazy_gettext("The team name is already taken")
   name = TextField(lazy_gettext('Team Name'),
                         [validators.Length(min=3, max=35, message=err_msg),
                          pb_validator.Unique(db.session, model.Team,
                                              model.Team.name, err_msg_2)])

   err_msg = lazy_gettext("Team Description must be between 3 and 35 characters long")
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=35, message=err_msg)])

    
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=35, message=err_msg)])

   public = BooleanField(lazy_gettext('Public'))

''' Modify Team '''
class UpdateTeamForm(Form):
   id = IntegerField(label=None, widget=HiddenInput())
   err_msg = lazy_gettext("Team Name must be between 3 and 35 characters long")
   err_msg_2 = lazy_gettext("The team name is already taken")
   name = TextField(lazy_gettext('Team Name'),
                         [validators.Length(min=3, max=35, message=err_msg),
                          pb_validator.Unique(db.session, model.Team,
                                              model.Team.name, err_msg_2)])

   err_msg = lazy_gettext("Team Description must be between 3 and 35 characters long")
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=35, message=err_msg)])

   public = BooleanField(lazy_gettext('Public'))

