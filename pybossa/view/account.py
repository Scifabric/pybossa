# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
"""
PyBossa Account view for web projects.

This module exports the following endpoints:
    * Accounts index: list of all registered users in PyBossa
    * Signin: method for signin into PyBossa
    * Signout: method for signout from PyBossa
    * Register: method for creating a new PyBossa account
    * Profile: method to manage user's profile (update data, reset password...)

"""
from itsdangerous import BadData
from markdown import markdown
import json
import time

from flask import Blueprint, request, url_for, flash, redirect, abort
from flask import render_template, current_app
from flask.ext.login import login_required, login_user, logout_user, \
    current_user
from flask.ext.mail import Message
from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired
from wtforms import TextField, PasswordField, validators, \
    IntegerField, SelectField, BooleanField
from wtforms.widgets import HiddenInput

import pybossa.validator as pb_validator
import pybossa.model as model
from flask.ext.babel import lazy_gettext, gettext
from sqlalchemy.sql import text
from pybossa.model.user import User
from pybossa.core import db, signer, mail, uploader, sentinel
from pybossa.util import Pagination, get_user_id_or_ip, pretty_date
from pybossa.util import get_user_signup_method
from pybossa.cache import users as cached_users

try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle


blueprint = Blueprint('account', __name__)


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    """
    Index page for all PyBossa registered users.

    Returns a Jinja2 rendered template with the users.

    """
    data = sentinel.slave.zrevrange('pybossa_feed', 0, 100, withscores=True)
    update_feed = []
    for u in data:
        tmp = pickle.loads(u[0])
        tmp['updated'] = u[1]
        if tmp.get('info'):
            tmp['info'] = json.loads(tmp['info'])
        update_feed.append(tmp)

    per_page = 24
    count = cached_users.get_total_users()
    accounts = cached_users.get_users_page(page, per_page)
    if not accounts and page != 1:
        abort(404)
    pagination = Pagination(page, per_page, count)
    if current_user.is_authenticated():
        user_id = current_user.id
    else:
        user_id = 'anonymous'
    top_users = cached_users.get_leaderboard(current_app.config['LEADERBOARD'],
                                             user_id)
    return render_template('account/index.html', accounts=accounts,
                           total=count,
                           top_users=top_users,
                           title="Community", pagination=pagination,
                           update_feed=update_feed)


class LoginForm(Form):

    """Login Form class for signin into PyBossa."""

    email = TextField(lazy_gettext('E-mail'),
                      [validators.Required(
                          message=lazy_gettext("The e-mail is required"))])

    password = PasswordField(lazy_gettext('Password'),
                             [validators.Required(
                                 message=lazy_gettext(
                                     "You must provide a password"))])


@blueprint.route('/signin', methods=['GET', 'POST'])
def signin():
    """
    Signin method for PyBossa users.

    Returns a Jinja2 template with the result of signing process.

    """
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        email = form.email.data
        user = model.user.User.query.filter_by(email_addr=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            msg_1 = gettext("Welcome back") + " " + user.fullname
            flash(msg_1, 'success')
            return redirect(request.args.get("next") or url_for("home.home"))
        elif user:
            msg, method = get_user_signup_method(user)
            if method == 'local':
                msg = gettext("Ooops, Incorrect email/password")
                flash(msg, 'error')
            else:
                flash(msg, 'info')
        else:
            msg = gettext("Ooops, we didn't find you in the system, \
                          did you sign in?")
            flash(msg, 'info')

    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    auth = {'twitter': False, 'facebook': False, 'google': False}
    if current_user.is_anonymous():
        # If Twitter is enabled in config, show the Twitter Sign in button
        if ('twitter' in current_app.blueprints): # pragma: no cover
            auth['twitter'] = True
        if ('facebook' in current_app.blueprints): # pragma: no cover
            auth['facebook'] = True
        if ('google' in current_app.blueprints): # pragma: no cover
            auth['google'] = True
        return render_template('account/signin.html',
                               title="Sign in",
                               form=form, auth=auth,
                               next=request.args.get('next'))
    else:
        # User already signed in, so redirect to home page
        return redirect(url_for("home.home"))


@blueprint.route('/signout')
def signout():
    """
    Signout PyBossa users.

    Returns a redirection to PyBossa home page.

    """
    logout_user()
    flash(gettext('You are now signed out'), 'success')
    return redirect(url_for('home.home'))


class RegisterForm(Form):

    """Register Form Class for creating an account in PyBossa."""

    err_msg = lazy_gettext("Full name must be between 3 and 35 "
                           "characters long")
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=35, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and 35 "
                           "characters long")
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('User name'),
                         [validators.Length(min=3, max=35, message=err_msg),
                          pb_validator.NotAllowedChars(),
                          pb_validator.Unique(db.session, model.user.User,
                                              model.user.User.name, err_msg_2)])

    err_msg = lazy_gettext("Email must be between 3 and 35 characters long")
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = TextField(lazy_gettext('Email Address'),
                           [validators.Length(min=3, max=35, message=err_msg),
                            validators.Email(),
                            pb_validator.Unique(
                                db.session, model.user.User,
                                model.user.User.email_addr, err_msg_2)])

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    password = PasswordField(lazy_gettext('New Password'),
                             [validators.Required(err_msg),
                              validators.EqualTo('confirm', err_msg_2)])

    confirm = PasswordField(lazy_gettext('Repeat Password'))


class UpdateProfileForm(Form):

    """Form Class for updating PyBossa's user Profile."""

    id = IntegerField(label=None, widget=HiddenInput())

    err_msg = lazy_gettext("Full name must be between 3 and 35 "
                           "characters long")
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=35, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and 35 "
                           "characters long")
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('Username'),
                     [validators.Length(min=3, max=35, message=err_msg),
                      pb_validator.NotAllowedChars(),
                      pb_validator.Unique(
                          db.session, model.user.User, model.user.User.name, err_msg_2)])

    err_msg = lazy_gettext("Email must be between 3 and 35 characters long")
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = TextField(lazy_gettext('Email Address'),
                           [validators.Length(min=3, max=35, message=err_msg),
                            validators.Email(),
                            pb_validator.Unique(
                                db.session, model.user.User,
                                model.user.User.email_addr, err_msg_2)])

    locale = SelectField(lazy_gettext('Language'))
    ckan_api = TextField(lazy_gettext('CKAN API Key'))
    privacy_mode = BooleanField(lazy_gettext('Privacy Mode'))

    def set_locales(self, locales):
        """Fill the locale.choices."""
        choices = []
        for locale in locales:
            if locale == 'en':
                lang = gettext("English")
            if locale == 'es':
                lang = gettext("Spanish")
            if locale == 'fr':
                lang = gettext("French")
            choices.append((locale, lang))
        self.locale.choices = choices


class AvatarUploadForm(Form):
    avatar = FileField(lazy_gettext('Avatar'), validators=[FileRequired()])
    x1 = IntegerField(label=None, widget=HiddenInput())
    y1 = IntegerField(label=None, widget=HiddenInput())
    x2 = IntegerField(label=None, widget=HiddenInput())
    y2 = IntegerField(label=None, widget=HiddenInput())



@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register method for creating a PyBossa account.

    Returns a Jinja2 template

    """
    # TODO: re-enable csrf
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        account = model.user.User(fullname=form.fullname.data,
                             name=form.name.data,
                             email_addr=form.email_addr.data)
        account.set_password(form.password.data)
        # account.locale = get_locale()
        db.session.add(account)
        db.session.commit()
        login_user(account, remember=True)
        flash(gettext('Thanks for signing-up'), 'success')
        return redirect(url_for('home.home'))
    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    return render_template('account/register.html',
                           title=gettext("Register"), form=form)


@blueprint.route('/profile', methods=['GET'])
def redirect_profile():
    if current_user.is_anonymous(): # pragma: no cover
        return redirect(url_for('.signin'))
    else:
        return redirect(url_for('.profile', name=current_user.name), 302)

@blueprint.route('/<name>/', methods=['GET'])
def profile(name):
    """
    Get user profile.

    Returns a Jinja2 template with the user information.

    """
    user = db.session.query(model.user.User).filter_by(name=name).first()

    if user is None:
        return abort(404)

    # Show public profile from another user
    if current_user.is_anonymous() or (user.id != current_user.id):
        user, apps_contributed, _ = cached_users.get_user_summary(name)
        apps_created, apps_draft = _get_user_apps(user['id'])
        if user:
            title = "%s &middot; User Profile" % user['fullname']
            return render_template('/account/public_profile.html',
                                   title=title,
                                   user=user,
                                   apps=apps_contributed,
                                   apps_created=apps_created)

    # Show user profile page with admin, as it is the same user
    if user.id == current_user.id and current_user.is_authenticated():
        sql = text('''
                   SELECT app.name, app.short_name, app.info,
                   COUNT(*) as n_task_runs
                   FROM task_run JOIN app ON
                   (task_run.app_id=app.id) WHERE task_run.user_id=:user_id
                   GROUP BY app.name, app.short_name, app.info
                   ORDER BY n_task_runs DESC;''')

        # results will have the following format
        # (app.name, app.short_name, n_task_runs)
        results = db.engine.execute(sql, user_id=current_user.id)

        apps_contrib = []
        for row in results:
            app = dict(name=row.name, short_name=row.short_name,
                       info=json.loads(row.info), n_task_runs=row.n_task_runs)
            apps_contrib.append(app)

        # Rank
        # See: https://gist.github.com/tokumine/1583695
        sql = text('''
                   WITH global_rank AS (
                        WITH scores AS (
                            SELECT user_id, COUNT(*) AS score FROM task_run
                            WHERE user_id IS NOT NULL GROUP BY user_id)
                        SELECT user_id, score, rank() OVER (ORDER BY score desc)
                        FROM scores)
                   SELECT * from global_rank WHERE user_id=:user_id;
                   ''')

        results = db.engine.execute(sql, user_id=current_user.id)
        for row in results:
            user.rank = row.rank
            user.score = row.score

        user.total = db.session.query(model.user.User).count()

        apps_published, apps_draft = _get_user_apps(current_user.id)

        return render_template('account/profile.html', title=gettext("Profile"),
                              apps_contrib=apps_contrib,
                              apps_published=apps_published,
                              apps_draft=apps_draft,
                              user=user)


@blueprint.route('/<name>/applications')
@login_required
def applications(name):
    """
    List user's project list.

    Returns a Jinja2 template with the list of projects of the user.

    """
    user = User.query.filter_by(name=name).first()
    if not user:
        return abort(404)
    if current_user.name != name:
        return abort(403)

    user = db.session.query(model.user.User).get(current_user.id)
    apps_published, apps_draft = _get_user_apps(user.id)

    return render_template('account/applications.html',
                           title=gettext("Projects"),
                           apps_published=apps_published,
                           apps_draft=apps_draft)


def _get_user_apps(user_id):
    apps_published = []
    apps_draft = []
    sql = text('''
               SELECT app.id, app.name, app.short_name, app.description,
               app.owner_id,
               app.info
               FROM app, task
               WHERE app.id=task.app_id AND app.owner_id=:user_id AND
               app.hidden=0 AND app.info LIKE('%task_presenter%')
               GROUP BY app.id, app.name, app.short_name,
               app.description,
               app.info;''')

    results = db.engine.execute(sql, user_id=user_id)
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   owner_id=row.owner_id,
                   description=row.description,
                   info=json.loads(row.info))
        apps_published.append(app)

    sql = text('''
               SELECT app.id, app.name, app.short_name, app.description,
               owner_id,
               app.info
               FROM app
               WHERE app.owner_id=:user_id
               AND app.info NOT LIKE('%task_presenter%')
               GROUP BY app.id, app.name, app.short_name,
               app.description,
               app.info;''')
    results = db.engine.execute(sql, user_id=user_id)
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   owner_id=row.owner_id,
                   description=row.description,
                   info=json.loads(row.info))
        apps_draft.append(app)
    return apps_published, apps_draft


@blueprint.route('/<name>/update', methods=['GET', 'POST'])
@login_required
def update_profile(name):
    """
    Update user's profile.

    Returns Jinja2 template.

    """
    user = User.query.filter_by(name=name).first()
    if not user:
        return abort(404)
    if current_user.id != user.id:
        return abort(403)
    show_passwd_form = True
    if user.twitter_user_id or user.google_user_id or user.facebook_user_id:
        show_passwd_form = False
    usr, apps, apps_created = cached_users.get_user_summary(name)
    # Extend the values
    current_user.rank = usr.get('rank')
    current_user.score = usr.get('score')
    # Title page
    title_msg = "Update your profile: %s" % current_user.fullname
    # Creation of forms
    update_form = UpdateProfileForm(obj=user)
    update_form.set_locales(current_app.config['LOCALES'])
    avatar_form = AvatarUploadForm()
    password_form = ChangePasswordForm()
    external_form = update_form


    if request.method == 'GET':
        return render_template('account/update.html',
                               title=title_msg,
                               user=usr,
                               form=update_form,
                               upload_form=avatar_form,
                               password_form=password_form,
                               external_form=external_form,
                               show_passwd_form=show_passwd_form)
    else:
        # Update user avatar
        if request.form.get('btn') == 'Upload':
            avatar_form = AvatarUploadForm()
            if avatar_form.validate_on_submit():
                file = request.files['avatar']
                coordinates = (avatar_form.x1.data, avatar_form.y1.data,
                               avatar_form.x2.data, avatar_form.y2.data)
                prefix = time.time()
                file.filename = "%s_avatar.png" % prefix
                container = "user_%s" % current_user.id
                uploader.upload_file(file,
                                     container=container,
                                     coordinates=coordinates)
                # Delete previous avatar from storage
                if current_user.info.get('avatar'):
                    uploader.delete_file(current_user.info['avatar'], container)
                current_user.info = {'avatar': file.filename,
                                     'container': container}
                db.session.commit()
                cached_users.delete_user_summary(current_user.name)
                flash(gettext('Your avatar has been updated! It may \
                              take some minutes to refresh...'), 'success')
                return redirect(url_for('.update_profile', name=current_user.name))
            else:
                flash("You have to provide an image file to update your avatar",
                      "error")
                return render_template('/account/update.html',
                                       form=update_form,
                                       upload_form=avatar_form,
                                       password_form=password_form,
                                       external_form=external_form,
                                       title=title_msg,
                                       show_passwd_form=show_passwd_form)
        # Update user profile
        elif request.form.get('btn') == 'Profile':
            update_form = UpdateProfileForm()
            update_form.set_locales(current_app.config['LOCALES'])
            if update_form.validate():
                current_user.id = update_form.id.data
                current_user.fullname = update_form.fullname.data
                current_user.name = update_form.name.data
                current_user.email_addr = update_form.email_addr.data
                current_user.privacy_mode = update_form.privacy_mode.data
                current_user.locale = update_form.locale.data
                db.session.commit()
                cached_users.delete_user_summary(current_user.name)
                flash(gettext('Your profile has been updated!'), 'success')
                return redirect(url_for('.update_profile', name=current_user.name))
            else:
                flash(gettext('Please correct the errors'), 'error')
                title_msg = 'Update your profile: %s' % current_user.fullname
                return render_template('/account/update.html',
                                       form=update_form,
                                       upload_form=avatar_form,
                                       password_form=password_form,
                                       external_form=external_form,
                                       title=title_msg,
                                       show_passwd_form=show_passwd_form)

        # Update user password
        elif request.form.get('btn') == 'Password':
            # Update the data because passing it in the constructor does not work
            update_form.name.data = user.name
            update_form.fullname.data = user.fullname
            update_form.email_addr.data = user.email_addr
            update_form.ckan_api.data = user.ckan_api
            external_form = update_form
            if password_form.validate_on_submit():
                user = db.session.query(model.user.User).get(current_user.id)
                if user.check_password(password_form.current_password.data):
                    user.set_password(password_form.new_password.data)
                    db.session.add(user)
                    db.session.commit()
                    flash(gettext('Yay, you changed your password succesfully!'),
                          'success')
                    return redirect(url_for('.update_profile', name=name))
                else:
                    msg = gettext("Your current password doesn't match the "
                                  "one in our records")
                    flash(msg, 'error')
                    return render_template('/account/update.html',
                                           form=update_form,
                                           upload_form=avatar_form,
                                           password_form=password_form,
                                           external_form=external_form,
                                           title=title_msg,
                                           show_passwd_form=show_passwd_form)
            else:
                flash(gettext('Please correct the errors'), 'error')
                return render_template('/account/update.html',
                                       form=update_form,
                                       upload_form=avatar_form,
                                       password_form=password_form,
                                       external_form=external_form,
                                       title=title_msg,
                                       show_passwd_form=show_passwd_form)
        # Update user external services
        elif request.form.get('btn') == 'External':
            del external_form.locale
            del external_form.email_addr
            del external_form.fullname
            del external_form.name
            if external_form.validate():
                current_user.ckan_api = external_form.ckan_api.data or None
                db.session.commit()
                cached_users.delete_user_summary(current_user.name)
                flash(gettext('Your profile has been updated!'), 'success')
                return redirect(url_for('.update_profile', name=current_user.name))
            else:
                flash(gettext('Please correct the errors'), 'error')
                title_msg = 'Update your profile: %s' % current_user.fullname
                return render_template('/account/update.html',
                                       form=update_form,
                                       upload_form=avatar_form,
                                       password_form=password_form,
                                       external_form=external_form,
                                       title=title_msg,
                                       show_passwd_form=show_passwd_form)
        # Otherwise return 415
        else:
            return abort(415)


class ChangePasswordForm(Form):

    """Form for changing user's password."""

    current_password = PasswordField(lazy_gettext('Current password'))

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat password'))


class ResetPasswordForm(Form):

    """Class for resetting user's password."""

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New Password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat Password'))


@blueprint.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Reset password method.

    Returns a Jinja2 template.

    """
    key = request.args.get('key')
    if key is None:
        abort(403)
    userdict = {}
    try:
        userdict = signer.signer.loads(key, max_age=3600, salt='password-reset')
    except BadData:
        abort(403)
    username = userdict.get('user')
    if not username or not userdict.get('password'):
        abort(403)
    user = model.user.User.query.filter_by(name=username).first_or_404()
    if user.passwd_hash != userdict.get('password'):
        abort(403)
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(gettext('You reset your password successfully!'), 'success')
        return redirect(url_for('.signin'))
    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    return render_template('/account/password_reset.html', form=form)


class ForgotPasswordForm(Form):

    """Form Class for forgotten password."""

    err_msg = lazy_gettext("Email must be between 3 and 35 characters long")
    email_addr = TextField(lazy_gettext('Email Address'),
                           [validators.Length(min=3, max=35, message=err_msg),
                            validators.Email()])


@blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Request a forgotten password for a user.

    Returns a Jinja2 template.

    """
    form = ForgotPasswordForm(request.form)
    if form.validate_on_submit():
        user = model.user.User.query\
                    .filter_by(email_addr=form.email_addr.data)\
                    .first()
        if user and user.email_addr:
            msg = Message(subject='Account Recovery',
                          recipients=[user.email_addr])
            if user.twitter_user_id:
                msg.body = render_template(
                    '/account/email/forgot_password_openid.md',
                    user=user, account_name='Twitter')
            elif user.facebook_user_id:
                msg.body = render_template(
                    '/account/email/forgot_password_openid.md',
                    user=user, account_name='Facebook')
            elif user.google_user_id:
                msg.body = render_template(
                    '/account/email/forgot_password_openid.md',
                    user=user, account_name='Google')
            else:
                userdict = {'user': user.name, 'password': user.passwd_hash}
                key = signer.signer.dumps(userdict, salt='password-reset')
                recovery_url = url_for('.reset_password',
                                       key=key, _external=True)
                msg.body = render_template(
                    '/account/email/forgot_password.md',
                    user=user, recovery_url=recovery_url)
            msg.html = markdown(msg.body)
            mail.send(msg)
            flash(gettext("We've send you email with account "
                          "recovery instructions!"),
                  'success')
        else:
            flash(gettext("We don't have this email in our records. "
                          "You may have signed up with a different "
                          "email or used Twitter, Facebook, or "
                          "Google to sign-in"), 'error')
    if request.method == 'POST' and not form.validate():
        flash(gettext('Something went wrong, please correct the errors on the '
              'form'), 'error')
    return render_template('/account/password_forgot.html', form=form)


@blueprint.route('/<name>/resetapikey', methods=['POST'])
@login_required
def reset_api_key(name):
    """
    Reset API-KEY for user.

    Returns a Jinja2 template.

    """
    user = User.query.filter_by(name=name).first()
    if not user:
        return abort(404)
    if current_user.name != user.name:
        return abort(403)

    title = ("User: %s &middot; Settings"
             "- Reset API KEY") % current_user.fullname
    user = db.session.query(model.user.User).get(current_user.id)
    user.api_key = model.make_uuid()
    db.session.commit()
    cached_users.delete_user_summary(user.name)
    msg = gettext('New API-KEY generated')
    flash(msg, 'success')
    return redirect(url_for('account.profile', name=name))
