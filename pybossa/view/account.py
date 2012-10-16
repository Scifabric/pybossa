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

from itsdangerous import BadData
from flask import Blueprint, request, url_for, flash, redirect, session, abort
from flask import render_template, current_app
from flaskext.login import login_required, login_user, logout_user,\
        current_user
from flaskext.wtf import Form, TextField, PasswordField, validators,\
        ValidationError, IntegerField, HiddenInput

import pybossa.model as model
from pybossa.core import db, signer
from pybossa.util import Unique
from pybossa.util import Pagination
from pybossa.util import Twitter
from pybossa.util import Facebook


blueprint = Blueprint('account', __name__)


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    per_page = 24
    count = db.session.query(model.User).count()
    accounts = db.session.query(model.User)\
                    .limit(per_page)\
                    .offset((page - 1) * per_page).all()
    if not accounts and page != 1:
        abort(404)
    pagination = Pagination(page, per_page, count)
    return render_template('account/index.html', accounts=accounts,
                           title="Community", pagination=pagination)


class LoginForm(Form):
    username = TextField('Username',
            [validators.Required(message="The username is required")])

    password = PasswordField('Password',
            [validators.Required(message="You must provide a password")])


@blueprint.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm(request.form)
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
    auth = {'twitter': False, 'facebook': False, 'google': False}
    if current_user.is_anonymous():
        # If Twitter is enabled in config, show the Twitter Sign in button
        if ('twitter' in current_app.blueprints):
                auth['twitter'] = True
        if ('facebook' in current_app.blueprints):
                auth['facebook'] = True
        if ('google' in current_app.blueprints):
                auth['google'] = True
        return render_template('account/signin.html', title="Sign in",
                form=form, auth=auth, next=request.args.get('next'))
    else:
        # User already signed in, so redirect to home page
        return redirect(url_for("home"))


@blueprint.route('/signout')
def signout():
    logout_user()
    flash('You are now signed out', 'success')
    return redirect(url_for('home'))


class RegisterForm(Form):
    fullname = TextField('Full name',
            [validators.Length(min=3, max=35,
                message="Full name must be between 3 and 35 characters long")])

    username = TextField('User name',
            [validators.Length(min=3, max=35,
                message="User name must be between 3 and 35 characters long"),
                Unique(db.session, model.User, model.User.name,
                    message="The user name is already taken")])

    email_addr = TextField('Email Address',
            [validators.Length(min=3, max=35,
                message="Email must be between 3 and 35 characters long"),
                validators.Email(),
                Unique(db.session, model.User, model.User.email_addr,
                    message="Email is already taken")])

    password = PasswordField('New Password',
            [validators.Required(message="Password cannot be empty"),
                validators.EqualTo('confirm', message='Passwords must match')])

    confirm = PasswordField('Repeat Password')


class UpdateProfileForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    fullname = TextField('Full name',
            [validators.Length(min=3, max=35,
                message="Full name must be between 3 and 35 characters long")])

    name = TextField('User name', [validators.Length(min=3, max=35,
        message="User name must be between 3 and 35 characters long"),
        Unique(db.session, model.User, model.User.name,
            message="The user name is already taken")])

    email_addr = TextField('Email Address',
            [validators.Length(min=3, max=35,
                message="Email must be between 3 and 35 characters long"),
             validators.Email(),
             Unique(db.session, model.User, model.User.email_addr,
                 message="Email is already taken")])


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # TODO: re-enable csrf
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        account = model.User(
            fullname=form.fullname.data,
            name=form.username.data,
            email_addr=form.email_addr.data
            )
        account.set_password(form.password.data)
        db.session.add(account)
        db.session.commit()
        login_user(account, remember=True)
        flash('Thanks for signing-up', 'success')
        return redirect(url_for('home'))
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('account/register.html',
            title="Register", form=form)


@blueprint.route('/profile', methods=['GET'])
@login_required
def profile():
    user = db.session.query(model.User).get(current_user.id)
    apps_published = []
    apps_draft = []
    apps_contrib = []
    # Sort the applications of the user
    for a in user.apps:
        if (len(a.tasks) > 0) and (a.info.get("task_presenter")):
            apps_published.append(a)
        else:
            apps_draft.append(a)

    # Check in which application the user has participated
    apps_contrib = db.session.query(model.App)\
            .join(model.App.task_runs)\
            .filter(model.TaskRun.user_id == user.id)\
            .distinct(model.TaskRun.app_id)\
            .all()
    for app in apps_contrib:
        c = db.session.query(model.TaskRun)\
                .filter(model.TaskRun.app_id == app.id)\
                .filter(model.TaskRun.user_id == user.id)\
                .count()
        app.c = c
        print app.c

    return render_template('account/profile.html', title="Profile",
            apps_published=apps_published,
            apps_draft=apps_draft,
            apps_contrib=apps_contrib,
            user=user)


@blueprint.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm(obj=current_user)
    form.populate_obj(current_user)
    if request.method == 'GET':
        return render_template('account/update.html',
                title="Update your profile: %s" % current_user.fullname,
                form=form)
    else:
        form = UpdateProfileForm(request.form)
        if form.validate():
            new_profile = model.User(
                    id=form.id.data,
                    fullname=form.fullname.data,
                    name=form.name.data,
                    email_addr=form.email_addr.data
                    )
            db.session.query(model.User)\
                    .filter(model.User.id == current_user.id)\
                    .first()
            db.session.merge(new_profile)
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('.profile'))
        else:
            flash('Please correct the errors', 'error')
            return render_template('/account/update.html', form=form,
                                    title='Update your profile: %s' %
                                            current_user.fullname)


class ChangePasswordForm(Form):
    current_password = PasswordField('Old Password')
    new_password = PasswordField('New Password',
            [validators.Required(message="Password cannot be empty"),
                validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')


@blueprint.route('/profile/password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        user = db.session.query(model.User).get(current_user.id)
        if user.check_password(form.current_password.data):
            user.set_password(form.new_password.data)
            db.session.add(user)
            db.session.commit()
            flash('Yay, you changed your password succesfully!', 'success')
            return redirect(url_for('.profile'))
        else:
            flash("Your current password doesn't match the one in our records", 'error')
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('/account/password.html', form=form)


class ResetPasswordForm(Form):
    new_password = PasswordField('New Password',
            [validators.Required(message="Password cannot be empty"),
                validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')


@blueprint.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    key = request.args.get('key')
    if key is None:
        abort(403)
    userdict = {}
    try:
        userdict = signer.loads(key, max_age=3600, salt='password-reset')
    except BadData:
        abort(403)
    username = userdict.get('user')
    if not username or not userdict.get('password'):
        abort(403)
    user = model.User.query.filter_by(name=username).first_or_404()
    if user.passwd_hash != userdict.get('password'):
        abort(403)
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        print "Changed password"
        flash('You reset your password successfully!', 'success')
        return redirect(url_for('.profile'))
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('/account/password_forgot.html', form=form)
