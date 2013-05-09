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
from pybossa.cache import users as cached_users

blueprint = Blueprint('team', __name__)

@blueprint.route('/<team_name>/users')
def users(team_name):
   """Manage users of team"""
   team  = model.Team.query.filter_by(owner=current_user.id).first()

   if team is None:
       flash("<strong>Ooops!</strong> We didn't find your group")
       return redirect(url_for('team.join'))

   # team_id
   usersteam = db.session.query(User2Team)\
                 .filter(User2Team.team_id == team.id)\
                 .all()

   if request.method == 'POST' and form.user.data:
       query = '%' + form.user.data.lower() + '%'
       found = db.session.query(model.User)\
                  .filter(or_(func.lower(model.User.name).like(query),
                              func.lower(model.User.fullname).like(query)))\
                  .filter(model.User.id != current_user.id)\
                  .all()
       if not found:
            flash("<strong>Ooops!</strong> We didn't find a user "
                  "matching your query: <strong>%s</strong>" % form.user.data)
       return render_template('/team/users.html', found=found, usersteam=usersteam,
                               title=lazy_gettext("Manage Tea, Users"), form=form)

   return render_template('/team/users.html', found=[], 
                           team=team,
                           usersteam=usersteam,
                           title=lazy_gettext("Manage Team Users"))
                           

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
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
        
       flash(lazy_gettext('Team successfully created'), 'success')
       return redirect(url_for('team.index', name=team.name))

   if request.method == 'POST' and not form.validate():
       flash(lazy_gettext('Please correct the errors'), 'error')
    
   return render_template('/team/register.html', form=form)

@blueprint.route('/join', methods=['GET', 'POST'])
@login_required
def join():
   # Populate the list with exits values
   sql = text('''select * from team t where not exists 
                 (select * from user2team ut 
                 where ut.team_id = t.id 
                 and user_id=:user_id)
              ''')
   teams = db.engine.execute(sql, user_id = current_user.id)

   # TODO:T re-enable csrf
   form = TeamUserForm(request.form)
   form.set_teams( teams )
   if request.method == 'POST' and form.validate():
       
       # Search data of the team
       team = model.Team.query.filter_by(id= int(form.team.data)).first()

       if team:   
           # Search for a possible  
           user2team = model.User2Team(
                             user_id = current_user.id,
                             team_id = team.id)

           # If the team is public or the current user is the owner of the group
           # the status will be enabled
           if team.public == True or team.owner == current_user.id: 
               flash( lazy_gettext('Association with the team successfully created!'), 'success')
               user2team.status = 1
           else:
               # Sending mail to the team owner
               user = db.session.query(model.User)\
                        .filter(model.User.id == team.owner)\
                        .first()

               msg = Message(subject='Pending request team', recipients=[user.email_addr])
               msg.body = render_template(
                   '/team/email/join_private_team.md',
                   user=user, userhost=current_user)
               msg.html = markdown(msg.body)
               mail.send(msg)

               flash( lazy_gettext('Association created, pending approval by the owner'), 'success')
 
           db.session.add(user2team)
           db.session.commit()

           return redirect(url_for('team.join'))
       else:
           flash(lazy_gettext('The team in the association doen\'t exists'), 'error')
           return redirect(url_for('team.join'))

   if request.method == 'POST' and not form.validate():
       flash(lazy_gettext('Please correct the errors'), 'error')


   users2team = model.User2Team.query\
                      .filter(User2Team.user_id == current_user.id) \
                      .all()

   return render_template('/team/join.html', form=form,
                                             users2team=users2team)

@blueprint.route('/join/<int:team_id>/delete')
@login_required
def joindelete(team_id=None):
   """Del current_user from team """
   if team_id:
       user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == current_user.id )\
                   .filter(User2Team.team_id == team_id )\
                   .first()

       if user2team:
            db.session.delete(user2team)
            db.session.commit()

            flash(lazy_gettext('Association with the team deleted'), 'success')
            return redirect(url_for('.join'))
       else:
            return abort(404)
   else:
       return abort(404)

@blueprint.route('/<team_name>/users/<int:user_id>/update')
@login_required
def userupdate(user_id=None, team_name=None):
   """Update association from one user to the team of current user owner"""

   if user_id:
       ''' Search team of current_user '''
       current_team  = model.Team.query.filter_by(owner=current_user.id).first()
      
       if current_team:
           ''' Check if exits association'''
           new_user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == user_id )\
                   .filter(User2Team.team_id == current_team.id )\
                   .first()

           if new_user2team:
               new_user2team.status = 1
               db.session.merge(new_user2team)
               db.session.commit()

               # Sending mail to the user
               user = db.session.query(model.User)\
                        .filter(model.User.id == user_id)\
                        .first()

               msg = Message(subject='Accept request team', recipients=[user.email_addr])
               recovery_url = ""
               msg.body = render_template(
                   '/team/email/join_private_accept.md',
                   user=user,team=current_team)
               msg.html = markdown(msg.body)
               mail.send(msg)

               flash(lazy_gettext('The user has been joined to the team correctly!'), 'success')
               return redirect(url_for('team.users', team_name=team_name))
           else:
               flash(lazy_gettext('I did not find the association'), 'error')
               return redirect(url_for('team.users', team_name=team_name))
       else:
           return abort(404)
   else:
       return abort(404)

@blueprint.route('/<team_name>/users/<int:user_id>/delete')
@login_required
def userdelete(user_id=None,team_name=None):
   '''Del association from one user to the team of current_user owner'''
   if user_id:
       ''' Search team of current_user '''
       current_team  = model.Team.query.filter_by(owner=current_user.id).first()

       if current_team:
           ''' Check if exits association'''
           user2team = db.session.query(User2Team)\
                   .filter(User2Team.user_id == user_id )\
                   .filter(User2Team.team_id == current_team.id )\
                   .first()

           if user2team:
               db.session.delete(user2team)
               db.session.commit()

               if current_team.owner != current_user.id:
                   # Sending mail to the user
                   user = db.session.query(model.User)\
                        .filter(model.User.id == user_id)\
                        .first()

                   msg = Message(subject='Refuse request team', recipients=[user.email_addr])
                   msg.body = render_template(
                       '/team/email/join_private_refuse.md',
                       user=user,team=current_team)
                   msg.html = markdown(msg.body)
                   mail.send(msg)

               flash(lazy_gettext('The user has been deleted from the team'), 'success')
               return redirect(url_for('team.users', team_name=team_name))
           else:
               flash(lazy_gettext('I didn\'t find the current association'), 'error')
               return redirect(url_for('team.users', team_name=team_name))
       else:
           return abort(404)
   else:
       return abort(404)

class TeamForm(Form):
   err_msg = lazy_gettext("Team Name must be between 3 and 50 characters long")
   err_msg_2 = lazy_gettext("The team name is already taken")
   name = TextField(lazy_gettext('Team Name'),
                         [validators.Length(min=3, max=50, message=err_msg),
                          pb_validator.Unique(db.session, model.Team,
                                              model.Team.name, err_msg_2)])

   err_msg = lazy_gettext("Team Description must be between 3 and 200 characters long")
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=200, message=err_msg)])

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
   err_msg = lazy_gettext("Team Name must be between 3 and 50 characters long")
   err_msg_2 = lazy_gettext("The team name is already taken")
   name = TextField(lazy_gettext('Team Name'),
                         [validators.Length(min=3, max=50, message=err_msg),
                          pb_validator.Unique(db.session, model.Team,
                                              model.Team.name, err_msg_2)])

   err_msg = lazy_gettext("Team Description must be between 3 and 200 characters long")
   description = TextField(lazy_gettext('Description'),
                         [validators.Length(min=3, max=200, message=err_msg)])

   public = BooleanField(lazy_gettext('Public'))

@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/<name>', methods=['GET', 'POST'])
@login_required
def index(name=None):
   ''' Details about the team owner of de current_user '''
  
   #if name:
   #    current_team  = model.Team.query.filter(Team.owner==current_user.id)\
   #                                    .filter(Team.name==name)\
   #                                    .first()
   #else:
       #current_team  = model.Team.query.filter(Team.owner==current_user.id)\
       #                                .first()

   current_team = None
   return render_template('/team/teams.html',
                           name=name,
                           current_team=None)

@blueprint.route('/<name>/delete', methods=['GET', 'POST'])
@login_required
def delete(name):
   ''' Delete the team owner of de current_user '''

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
   user_team  = model.Team.query.filter(Team.owner==current_user.id)\
                                .filter(Team.name==name)\
                                .first()

   #current_team  = model.Team.query.filter_by(owner=current_user.id).first()
   #team  = model.Team.query.filter_by(owner=current_user.id).first()

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
                                     public=form.public.data,
                                     owner=current_user.id)

               db.session.merge(new_profile)
               db.session.commit()
            
               flash(lazy_gettext('Your team has been updated!'), 'success')
               return redirect(url_for('team.index', name=new_profile.name))
           else:
               flash(lazy_gettext('Please correct the errors'), 'error')
               title_msg = 'Update team: %s' % user_team.name
               return render_template('/team/update.html', form=form,
                                   title=title_msg)
   else:
       flash(lazy_gettext('Oopps, The group that you try to update doesn\t exists or you don\t are the owner.'), 'error')
       title_msg = 'Update team: '
       return redirect(url_for('team.index'))

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
