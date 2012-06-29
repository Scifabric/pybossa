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

from flask import Blueprint, request, url_for, flash, redirect, session
from flask import render_template, current_app
from flaskext.login import login_required, login_user, logout_user, current_user
from flaskext.wtf import Form, TextField, PasswordField, validators, ValidationError, IntegerField, HiddenInput

import pybossa.model as model
from pybossa.util import Unique
from pybossa.util import Pagination
from pybossa.util import Twitter
from pybossa.util import Facebook

blueprint = Blueprint('account', __name__)



@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    per_page = 24
    count = model.Session.query(model.User).count()
    accounts = model.Session.query(model.User)\
                    .limit(per_page)\
                    .offset((page - 1) * per_page).all()
    if not accounts and page!= 1:
        abort(404)
    pagination = Pagination(page, per_page, count)
    return render_template('account/index.html', accounts = accounts, 
                           title = "Community", pagination = pagination)
    
class LoginForm(Form):
    username = TextField('Username', [validators.Required(message="The username is required")])
    password = PasswordField('Password', [validators.Required(message="You must provide a password")])

@blueprint.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        username = form.username.data
        user = model.User.by_name(username)
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash("Welcome back %s" % user.fullname, 'success')
            return redirect(request.args.get("next") or url_for("home"))
        else:
            flash('Incorrect email/password', 'error')

    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    auth = {'twitter': False, 'facebook': False}
    if current_user.is_anonymous():
        # If Twitter is enabled in config, show the Twitter Sign in button
        if ('twitter' in current_app.blueprints):
                auth['twitter'] = True
        if ('facebook' in current_app.blueprints):
                auth['facebook'] = True
                #return render_template('account/signin.html', title="Sign in", form=form, auth=auth, next=request.args.get('next'))
        # Else use only the default system
        #else:
        return render_template('account/signin.html', title="Sign in", form=form, auth=auth, next=request.args.get('next'))
    else:
        # User already signed in, so redirect to home page
        return redirect(url_for("home"))

@blueprint.route('/signout')
def signout():
    logout_user()
    flash('You are now signed out', 'success')
    return redirect(url_for('home'))


class RegisterForm(Form):
    fullname = TextField('Full name', [validators.Length(min=3, max=35, message="Full name must be between 3 and 35 characters long")])
    username = TextField('User name', [validators.Length(min=3, max=35, message="User name must be between 3 and 35 characters long"),
                                       Unique(model.Session, model.User, model.User.name, message="The user name is already taken")
                                      ])
    email_addr = TextField('Email Address', [validators.Length(min=3, max=35, message="Email must be between 3 and 35 characters long"),
                                             validators.Email(),
                                             Unique(model.Session, model.User, model.User.email_addr, message="Email is already taken")])
    password = PasswordField('New Password', [
        validators.Required(message="Password cannot be empty"),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

class UpdateProfileForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    fullname = TextField('Full name', [validators.Length(min=3, max=35, message="Full name must be between 3 and 35 characters long")])
    name = TextField('User name', [validators.Length(min=3, max=35, message="User name must be between 3 and 35 characters long"),
                                       Unique(model.Session, model.User, model.User.name, message="The user name is already taken")
                                      ])
    email_addr = TextField('Email Address', [validators.Length(min=3, max=35, message="Email must be between 3 and 35 characters long"),
                                             validators.Email(),
                                             Unique(model.Session, model.User, model.User.email_addr, message="Email is already taken")])


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # TODO: re-enable csrf
    form = RegisterForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        account = model.User(
            fullname=form.fullname.data,
            name=form.username.data,
            email_addr=form.email_addr.data
            )
        account.set_password(form.password.data)
        model.Session.add(account)
        model.Session.commit()
        login_user(account, remember=True)
        flash('Thanks for signing-up', 'success')
        return redirect(url_for('home'))
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('account/register.html', title="Register", form=form)

@blueprint.route('/profile', methods = ['GET'])
@login_required
def profile():
    user = model.Session.query(model.User).get(current_user.id)

    return render_template('account/profile.html', title="Profile", user = user)

@blueprint.route('/profile/update', methods = ['GET','POST'])
@login_required
def update_profile():
    form = UpdateProfileForm(obj = current_user, csrf_enabled = False)
    form.populate_obj(current_user)
    if request.method == 'GET':
        return render_template('account/update.html', 
                title="Update your profile: %s" % current_user.fullname, 
                form = form)
    else:
        form = UpdateProfileForm(request.form, csrf_enabled = False)
        if form.validate():
            new_profile = model.User(
                    id = form.id.data,
                    fullname = form.fullname.data,
                    name = form.name.data,
                    email_addr = form.email_addr.data
                    )
            user = model.Session.query(model.User).filter(model.User.id == current_user.id).first()
            model.Session.merge(new_profile)
            model.Session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('.profile'))
        else:
            flash('Please correct the errors', 'error')
            return render_template('/account/update.html', form = form,
                                    title = 'Update your profile: %s' % current_user.fullname)
                                    

