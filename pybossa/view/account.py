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

import pybossa.model as model
from flask.ext.babel import gettext
from sqlalchemy.sql import text
from pybossa.model.user import User
from pybossa.core import db, signer, mail, uploader, sentinel
from pybossa.util import Pagination, get_user_id_or_ip, pretty_date
from pybossa.util import get_user_signup_method
from pybossa.cache import users as cached_users
from pybossa.cache import apps as cached_apps
from pybossa.auth import require

from pybossa.forms.account_view_forms import *

try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle


blueprint = Blueprint('account', __name__)

from pybossa.repositories import UserRepository
user_repo = UserRepository(db)


def get_update_feed():
    """Return update feed list."""
    data = sentinel.slave.zrevrange('pybossa_feed', 0, 99, withscores=True)
    update_feed = []
    for u in data:
        tmp = pickle.loads(u[0])
        tmp['updated'] = u[1]
        if tmp.get('info') and type(tmp.get('info')) == unicode:
            tmp['info'] = json.loads(tmp['info'])
        update_feed.append(tmp)
    return update_feed

@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    """
    Index page for all PyBossa registered users.

    Returns a Jinja2 rendered template with the users.

    """
    update_feed = get_update_feed()
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
        user = user_repo.get_by(email_addr=email)
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


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register method for creating a PyBossa account.

    Returns a Jinja2 template

    """
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        account = dict(fullname=form.fullname.data, name=form.name.data,
                       email_addr=form.email_addr.data, password=form.password.data)
        key = signer.dumps(account, salt='account-validation')
        confirm_url = url_for('.confirm_account', key=key, _external=True)
        if current_app.config.get('ACCOUNT_CONFIRMATION_DISABLED'):
            return redirect(confirm_url)
        msg = Message(subject='Welcome to %s!' % current_app.config.get('BRAND'),
                          recipients=[account['email_addr']])
        msg.body = render_template('/account/email/validate_account.md',
                                    user=account, confirm_url=confirm_url)
        msg.html = markdown(msg.body)
        mail.send(msg)
        return render_template('account/account_validation.html')
    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    return render_template('account/register.html',
                           title=gettext("Register"), form=form)


@blueprint.route('/register/confirmation', methods=['GET'])
def confirm_account():
    key = request.args.get('key')
    if key is None:
        abort(403)
    try:
        userdict = signer.loads(key, max_age=3600, salt='account-validation')
    except BadData:
        abort(403)
    account = model.user.User(fullname=userdict['fullname'],
                              name=userdict['name'],
                              email_addr=userdict['email_addr'])
    account.set_password(userdict['password'])
    user_repo.save(account)
    login_user(account, remember=True)
    flash(gettext('Thanks for signing-up'), 'success')
    return redirect(url_for('home.home'))


@blueprint.route('/profile', methods=['GET'])
def redirect_profile():
    if current_user.is_anonymous(): # pragma: no cover
        return redirect(url_for('.signin'))
    return redirect(url_for('.profile', name=current_user.name), 302)


@blueprint.route('/<name>/', methods=['GET'])
def profile(name):
    """
    Get user profile.

    Returns a Jinja2 template with the user information.

    """
    user = user_repo.get_by_name(name=name)
    if user is None:
        raise abort(404)
    if current_user.is_anonymous() or (user.id != current_user.id):
        return _show_public_profile(user)
    if current_user.is_authenticated() and user.id == current_user.id:
        return _show_own_profile(user)


def _show_public_profile(user):
    user_dict = cached_users.get_user_summary(user.name)
    apps_contributed = cached_users.apps_contributed_cached(user.id)
    apps_created = cached_users.published_apps_cached(user.id)
    if current_user.is_authenticated() and current_user.admin:
        apps_hidden = cached_users.hidden_apps(user.id)
        apps_created.extend(apps_hidden)
    if user_dict:
        title = "%s &middot; User Profile" % user_dict['fullname']
        return render_template('/account/public_profile.html',
                               title=title,
                               user=user_dict,
                               apps=apps_contributed,
                               apps_created=apps_created)


def _show_own_profile(user):
    rank_and_score = cached_users.rank_and_score(user.id)
    user.rank = rank_and_score['rank']
    user.score = rank_and_score['score']
    user.total = cached_users.get_total_users()
    apps_contributed = cached_users.apps_contributed(user.id)
    apps_published, apps_draft = _get_user_apps(user.id)
    apps_published.extend(cached_users.hidden_apps(user.id))

    return render_template('account/profile.html', title=gettext("Profile"),
                          apps_contrib=apps_contributed,
                          apps_published=apps_published,
                          apps_draft=apps_draft,
                          user=cached_users.get_user_summary(user.name))



@blueprint.route('/<name>/applications')
@login_required
def applications(name):
    """
    List user's project list.

    Returns a Jinja2 template with the list of projects of the user.

    """
    user = user_repo.get_by_name(name)
    if not user:
        return abort(404)
    if current_user.name != name:
        return abort(403)

    user = user_repo.get(current_user.id)
    apps_published, apps_draft = _get_user_apps(user.id)
    apps_published.extend(cached_users.hidden_apps(user.id))

    return render_template('account/applications.html',
                           title=gettext("Projects"),
                           apps_published=apps_published,
                           apps_draft=apps_draft)


def _get_user_apps(user_id):
    apps_published = cached_users.published_apps(user_id)
    apps_draft = cached_users.draft_apps(user_id)
    return apps_published, apps_draft



@blueprint.route('/<name>/update', methods=['GET', 'POST'])
@login_required
def update_profile(name):
    """
    Update user's profile.

    Returns Jinja2 template.

    """
    user = user_repo.get_by_name(name)
    if not user:
        return abort(404)
    require.user.update(user)
    show_passwd_form = True
    if user.twitter_user_id or user.google_user_id or user.facebook_user_id:
        show_passwd_form = False
    usr = cached_users.get_user_summary(name)
    # Extend the values
    user.rank = usr.get('rank')
    user.score = usr.get('score')
    # Title page
    title_msg = "Update your profile: %s" % user.fullname
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
                container = "user_%s" % user.id
                uploader.upload_file(file,
                                     container=container,
                                     coordinates=coordinates)
                # Delete previous avatar from storage
                if user.info.get('avatar'):
                    uploader.delete_file(user.info['avatar'], container)
                user.info = {'avatar': file.filename,
                                     'container': container}
                user_repo.update(user)
                cached_users.delete_user_summary(user.name)
                flash(gettext('Your avatar has been updated! It may \
                              take some minutes to refresh...'), 'success')
                return redirect(url_for('.update_profile', name=user.name))
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
                user.id = update_form.id.data
                user.fullname = update_form.fullname.data
                user.name = update_form.name.data
                user.email_addr = update_form.email_addr.data
                user.privacy_mode = update_form.privacy_mode.data
                user.locale = update_form.locale.data
                user_repo.update(user)
                cached_users.delete_user_summary(user.name)
                flash(gettext('Your profile has been updated!'), 'success')
                return redirect(url_for('.update_profile', name=user.name))
            else:
                flash(gettext('Please correct the errors'), 'error')
                title_msg = 'Update your profile: %s' % user.fullname
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
                user = user_repo.get(user.id)
                if user.check_password(password_form.current_password.data):
                    user.set_password(password_form.new_password.data)
                    user_repo.update(user)
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
                user.ckan_api = external_form.ckan_api.data or None
                user_repo.update(user)
                cached_users.delete_user_summary(user.name)
                flash(gettext('Your profile has been updated!'), 'success')
                return redirect(url_for('.update_profile', name=user.name))
            else:
                flash(gettext('Please correct the errors'), 'error')
                title_msg = 'Update your profile: %s' % user.fullname
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
        userdict = signer.loads(key, max_age=3600, salt='password-reset')
    except BadData:
        abort(403)
    username = userdict.get('user')
    if not username or not userdict.get('password'):
        abort(403)
    user = user_repo.get_by_name(username)
    if user.passwd_hash != userdict.get('password'):
        abort(403)
    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        user_repo.update(user)
        login_user(user)
        flash(gettext('You reset your password successfully!'), 'success')
        return redirect(url_for('.signin'))
    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    return render_template('/account/password_reset.html', form=form)


@blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Request a forgotten password for a user.

    Returns a Jinja2 template.

    """
    form = ForgotPasswordForm(request.form)
    if form.validate_on_submit():
        user = user_repo.get_by(email_addr=form.email_addr.data)
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
                key = signer.dumps(userdict, salt='password-reset')
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
    user = user_repo.get_by_name(name)
    if not user:
        return abort(404)
    require.user.update(user)
    title = ("User: %s &middot; Settings"
             "- Reset API KEY") % current_user.fullname
    user.api_key = model.make_uuid()
    user_repo.update(user)
    cached_users.delete_user_summary(user.name)
    msg = gettext('New API-KEY generated')
    flash(msg, 'success')
    return redirect(url_for('account.profile', name=name))
