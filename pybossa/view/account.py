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
from flask import render_template
from flaskext.login import login_required, login_user, logout_user, current_user
from flaskext.wtf import Form, TextField, PasswordField, validators, ValidationError, IntegerField, HiddenInput

import pybossa.model as model
from pybossa.util import Unique
from pybossa.util import Twitter
import settings_local as config

blueprint = Blueprint('account', __name__)

@blueprint.route('/')
def index():
    accounts = model.Session.query(model.User).all()
    return render_template('account/index.html', accounts = accounts, title = "Community")
    
class LoginForm(Form):
    username = TextField('Username', [validators.Required(message="The username is required")])
    password = PasswordField('Password', [validators.Required(message="You must provide a password")])

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
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
    auth = {'twitter': False}
    if current_user.is_anonymous():
        try:
            twitter
            auth['twitter'] = True
            return render_template('account/login.html', title="Login", form=form, auth=auth, next=request.args.get('next'))
        except NameError:
            return render_template('account/login.html', title="Login", form=form, auth=auth, next=request.args.get('next'))
    else:
        # User already signed in, so redirect to home page
        return redirect(url_for("home"))


try:
    twitter = Twitter(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
    @blueprint.route('/twitter', methods=['GET','POST'])
    def login_twitter():
        return twitter.oauth.authorize(callback=url_for('.oauth_authorized',
                next=request.args.get("next") ))
    
    @twitter.oauth.tokengetter
    def get_twitter_token():
        if current_user.is_anonymous(): 
            return None
        else:
            return((current_user.info['twitter_token']['oauth_token'], 
                   current_user.info['twitter_token']['oauth_token_secret'])) 
    
    @blueprint.route('/oauth-authorized')
    @twitter.oauth.authorized_handler
    def oauth_authorized(resp):
        """Called after authorization. After this function finished handling,
        the OAuth information is removed from the session again. When this
        happened, the tokengetter from above is used to retrieve the oauth
        token and secret.
        
        Because the remote application could have re-authorized the application
        it is necessary to update the values in the database.
        
        If the application redirected back after denying, the response passed
        to the function will be `None`. Otherwise a dictionary with the values
        the application submitted. Note that Twitter itself does not really
        redirect back unless the user clicks on the application name.
        """
        next_url = request.args.get('next') or url_for('home')
        if resp is None:
            flash(u'You denied the request to sign in.', 'error')
            return redirect(next_url)
    
        user = model.Session.query(model.User).filter_by(twitter_user_id = resp['user_id']).first()
    
        # user never signed on
        # Twitter API does not provide a way to get the e-mail so we will ask for it
        # only the first time
        request_email = False
        first_login = False
        if user is None:
            request_email = True
            first_login = True
            twitter_token = dict(
                    oauth_token = resp['oauth_token'],
                    oauth_token_secret = resp['oauth_token_secret']
                    )
            info = dict(twitter_token = twitter_token)
            user = model.User(
                    fullname = resp['screen_name'],
                    name = resp['screen_name'],
                    email_addr = 'None',
                    twitter_user_id = resp['user_id'],
                    info = info 
                    )
            model.Session.add(user)
            model.Session.commit()
    
        login_user(user, remember=True)
        flash("Welcome back %s" % user.fullname, 'success')
        if (user.email_addr == "None"): request_email = True

        if request_email:
            if first_login:
                flash("This is your first login, please add a valid e-mail")
            else:
                flash("Please update your e-mail address in your profile page")
            return redirect(url_for('.update_profile'))

        return redirect(next_url)
except:
    print "Twitter CONSUMER_KEY and CONSUMER_SECRET not available in the config file"
    print "Twitter login disabled"

@blueprint.route('/logout')
def logout():
    logout_user()
    flash('You are now logged out', 'success')
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
    return render_template('account/profile.html', title="Profile")

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
                                    

