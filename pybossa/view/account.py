# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""
PYBOSSA Account view for web projects.

This module exports the following endpoints:
    * Accounts index: list of all registered users in PYBOSSA
    * Signin: method for signin into PYBOSSA
    * Signout: method for signout from PYBOSSA
    * Register: method for creating a new PYBOSSA account
    * Profile: method to manage user's profile (update data, reset password...)

"""
from itsdangerous import BadData
from markdown import markdown
import time

from flask import Blueprint, request, url_for, flash, redirect, abort
from flask import render_template, current_app
from flask.ext.login import login_required, login_user, logout_user, \
    current_user
from rq import Queue

import pybossa.model as model
from flask.ext.babel import gettext
from flask_wtf.csrf import generate_csrf
from flask import jsonify
from pybossa.core import signer, uploader, sentinel, newsletter
from pybossa.util import Pagination, handle_content_type
from pybossa.util import get_user_signup_method
from pybossa.util import redirect_content_type
from pybossa.util import get_avatar_url
from pybossa.cache import users as cached_users
from pybossa.auth import ensure_authorized_to
from pybossa.jobs import send_mail
from pybossa.core import user_repo
from pybossa.feed import get_update_feed
from pybossa.messages import *

from pybossa.forms.account_view_forms import *


blueprint = Blueprint('account', __name__)

mail_queue = Queue('email', connection=sentinel.master)


@blueprint.route('/')
@blueprint.route('/page/<int:page>')
def index(page=1):
    """Index page for all PYBOSSA registered users."""

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
        user_id = None
    top_users = cached_users.get_leaderboard(current_app.config['LEADERBOARD'],
                                             user_id)
    tmp = dict(template='account/index.html', accounts=accounts,
               total=count,
               top_users=top_users,
               title="Community", pagination=pagination,
               update_feed=update_feed)
    return handle_content_type(tmp)


@blueprint.route('/signin', methods=['GET', 'POST'])
def signin():
    """
    Signin method for PYBOSSA users.

    Returns a Jinja2 template with the result of signing process.

    """
    form = LoginForm(request.body)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        email = form.email.data
        user = user_repo.get_by(email_addr=email)
        if user and user.check_password(password):
            msg_1 = gettext("Welcome back") + " " + user.fullname
            flash(msg_1, 'success')
            return _sign_in_user(user)
        elif user:
            msg, method = get_user_signup_method(user)
            if method == 'local':
                msg = gettext("Ooops, Incorrect email/password")
                flash(msg, 'error')
            else:
                flash(msg, 'info')
        else:
            msg = gettext("Ooops, we didn't find you in the system, \
                          did you sign up?")
            flash(msg, 'info')

    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    auth = {'twitter': False, 'facebook': False, 'google': False}
    if current_user.is_anonymous():
        # If Twitter is enabled in config, show the Twitter Sign in button
        if ('twitter' in current_app.blueprints):  # pragma: no cover
            auth['twitter'] = True
        if ('facebook' in current_app.blueprints):  # pragma: no cover
            auth['facebook'] = True
        if ('google' in current_app.blueprints):  # pragma: no cover
            auth['google'] = True
        response = dict(template='account/signin.html',
                        title="Sign in",
                        form=form,
                        auth=auth,
                        next=request.args.get('next'))
        return handle_content_type(response)
    else:
        # User already signed in, so redirect to home page
        return redirect_content_type(url_for("home.home"))


def _sign_in_user(user):
    login_user(user, remember=True)
    if newsletter.ask_user_to_subscribe(user):
        return redirect_content_type(url_for('account.newsletter_subscribe',
                                             next=request.args.get('next')))
    return redirect_content_type(request.args.get("next") or
                                 url_for("home.home"))


@blueprint.route('/signout')
def signout():
    """
    Signout PYBOSSA users.

    Returns a redirection to PYBOSSA home page.

    """
    logout_user()
    flash(gettext('You are now signed out'), SUCCESS)
    return redirect_content_type(url_for('home.home'), status=SUCCESS)


def get_email_confirmation_url(account):
    """Return confirmation url for a given user email."""
    key = signer.dumps(account, salt='account-validation')
    confirm_url = url_for('.confirm_account', key=key, _external=True)
    return confirm_url


@blueprint.route('/confirm-email')
@login_required
def confirm_email():
    """Send email to confirm user email."""
    acc_conf_dis = current_app.config.get('ACCOUNT_CONFIRMATION_DISABLED')
    if acc_conf_dis:
        return abort(404)
    if current_user.valid_email is False:
        user = user_repo.get(current_user.id)
        account = dict(fullname=current_user.fullname, name=current_user.name,
                       email_addr=current_user.email_addr)
        confirm_url = get_email_confirmation_url(account)
        subject = ('Verify your email in %s' % current_app.config.get('BRAND'))
        msg = dict(subject=subject,
                   recipients=[current_user.email_addr],
                   body=render_template('/account/email/validate_email.md',
                                        user=account, confirm_url=confirm_url))
        msg['html'] = render_template('/account/email/validate_email.html',
                                      user=account, confirm_url=confirm_url)
        mail_queue.enqueue(send_mail, msg)
        msg = gettext("An e-mail has been sent to \
                       validate your e-mail address.")
        flash(msg, 'info')
        user.confirmation_email_sent = True
        user_repo.update(user)
    return redirect_content_type(url_for('.profile', name=current_user.name))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register method for creating a PYBOSSA account.

    Returns a Jinja2 template

    """
    form = RegisterForm(request.body)
    if request.method == 'POST' and form.validate():
        account = dict(fullname=form.fullname.data, name=form.name.data,
                       email_addr=form.email_addr.data,
                       password=form.password.data)
        confirm_url = get_email_confirmation_url(account)
        if current_app.config.get('ACCOUNT_CONFIRMATION_DISABLED'):
            return _create_account(account)
        msg = dict(subject='Welcome to %s!' % current_app.config.get('BRAND'),
                   recipients=[account['email_addr']],
                   body=render_template('/account/email/validate_account.md',
                                        user=account, confirm_url=confirm_url))
        msg['html'] = markdown(msg['body'])
        mail_queue.enqueue(send_mail, msg)
        data = dict(template='account/account_validation.html',
                    title=gettext("Account validation"),
                    status='sent')
        return handle_content_type(data)
    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    data = dict(template='account/register.html',
                title=gettext("Register"), form=form)
    return handle_content_type(data)


@blueprint.route('/newsletter')
@login_required
def newsletter_subscribe():
    """
    Register method for subscribing user to PYBOSSA newsletter.

    Returns a Jinja2 template

    """
    # Save that we've prompted the user to sign up in the newsletter
    if newsletter.is_initialized() and current_user.is_authenticated():
        next_url = request.args.get('next') or url_for('home.home')
        user = user_repo.get(current_user.id)
        if current_user.newsletter_prompted is False:
            user.newsletter_prompted = True
            user_repo.update(user)
        if request.args.get('subscribe') == 'True':
            newsletter.subscribe_user(user)
            flash("You are subscribed to our newsletter!", 'success')
            return redirect_content_type(next_url)
        elif request.args.get('subscribe') == 'False':
            return redirect_content_type(next_url)
        else:
            response = dict(template='account/newsletter.html',
                            title=gettext("Subscribe to our Newsletter"),
                            next=next_url)
            return handle_content_type(response)
    else:
        return abort(404)


@blueprint.route('/register/confirmation', methods=['GET'])
def confirm_account():
    """Confirm account endpoint."""
    key = request.args.get('key')
    if key is None:
        abort(403)
    try:
        timeout = current_app.config.get('ACCOUNT_LINK_EXPIRATION', 3600)
        userdict = signer.loads(key, max_age=timeout, salt='account-validation')
    except BadData:
        abort(403)
    # First check if the user exists
    user = user_repo.get_by_name(userdict['name'])
    if user is not None:
        return _update_user_with_valid_email(user, userdict['email_addr'])
    return _create_account(userdict)


def _create_account(user_data):
    new_user = model.user.User(fullname=user_data['fullname'],
                               name=user_data['name'],
                               email_addr=user_data['email_addr'],
                               valid_email=True)
    new_user.set_password(user_data['password'])
    user_repo.save(new_user)
    flash(gettext('Thanks for signing-up'), 'success')
    return _sign_in_user(new_user)


def _update_user_with_valid_email(user, email_addr):
    user.valid_email = True
    user.confirmation_email_sent = False
    user.email_addr = email_addr
    user_repo.update(user)
    flash(gettext('Your email has been validated.'))
    return _sign_in_user(user)


@blueprint.route('/profile', methods=['GET'])
def redirect_profile():
    """Redirect method for profile."""
    if current_user.is_anonymous():  # pragma: no cover
        return redirect_content_type(url_for('.signin'), status='not_signed_in')
    if (request.headers.get('Content-Type') == 'application/json') and current_user.is_authenticated():
        return _show_own_profile(current_user)
    else:
        return redirect_content_type(url_for('.profile', name=current_user.name))


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
    user_dict = cached_users.public_get_user_summary(user.name)
    projects_contributed = cached_users.public_projects_contributed_cached(user.id)
    projects_created = cached_users.public_published_projects_cached(user.id)

    if current_user.is_authenticated() and current_user.admin:
        draft_projects = cached_users.draft_projects(user.id)
        projects_created.extend(draft_projects)
    title = "%s &middot; User Profile" % user_dict['fullname']

    response = dict(template='/account/public_profile.html',
                    title=title,
                    user=user_dict,
                    projects=projects_contributed,
                    projects_created=projects_created)

    return handle_content_type(response)


def _show_own_profile(user):
    user_dict = cached_users.get_user_summary(user.name)
    rank_and_score = cached_users.rank_and_score(user.id)
    user.rank = rank_and_score['rank']
    user.score = rank_and_score['score']
    user.total = cached_users.get_total_users()
    projects_contributed = cached_users.public_projects_contributed_cached(user.id)
    projects_published, projects_draft = _get_user_projects(user.id)
    cached_users.get_user_summary(user.name)

    response = dict(template='account/profile.html', title=gettext("Profile"),
                    projects_contrib=projects_contributed,
                    projects_published=projects_published,
                    projects_draft=projects_draft,
                    user=user_dict)

    return handle_content_type(response)


@blueprint.route('/<name>/applications')
@blueprint.route('/<name>/projects')
@login_required
def projects(name):
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
    projects_published, projects_draft = _get_user_projects(user.id)

    response = dict(template='account/projects.html',
                    title=gettext("Projects"),
                    projects_published=projects_published,
                    projects_draft=projects_draft)
    return handle_content_type(response)


def _get_user_projects(user_id):
    projects_published = cached_users.published_projects(user_id)
    projects_draft = cached_users.draft_projects(user_id)
    return projects_published, projects_draft


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
    ensure_authorized_to('update', user)
    show_passwd_form = True
    if user.twitter_user_id or user.google_user_id or user.facebook_user_id:
        show_passwd_form = False
    usr = cached_users.get_user_summary(name)
    # Extend the values
    user.rank = usr.get('rank')
    user.score = usr.get('score')
    if request.body.get('btn') != 'Profile':
        update_form = UpdateProfileForm(formdata=None, obj=user)
    else:
        update_form = UpdateProfileForm(obj=user)
    update_form.set_locales(current_app.config['LOCALES'])
    avatar_form = AvatarUploadForm()
    password_form = ChangePasswordForm()

    title_msg = "Update your profile: %s" % user.fullname

    if request.method == 'POST':
        # Update user avatar
        succeed = False
        if request.body.get('btn') == 'Upload':
            succeed = _handle_avatar_update(user, avatar_form)
        # Update user profile
        elif request.body.get('btn') == 'Profile':
            succeed = _handle_profile_update(user, update_form)
        # Update user password
        elif request.body.get('btn') == 'Password':
            succeed = _handle_password_update(user, password_form)
        # Update user external services
        elif request.body.get('btn') == 'External':
            succeed = _handle_external_services_update(user, update_form)
        # Otherwise return 415
        else:
            return abort(415)
        if succeed:
            return redirect_content_type(url_for('.update_profile',
                                                 name=user.name),
                                         status=SUCCESS)
        else:
            data = dict(template='/account/update.html',
                        form=update_form,
                        upload_form=avatar_form,
                        password_form=password_form,
                        title=title_msg,
                        show_passwd_form=show_passwd_form)
            return handle_content_type(data)

    data = dict(template='/account/update.html',
                form=update_form,
                upload_form=avatar_form,
                password_form=password_form,
                title=title_msg,
                show_passwd_form=show_passwd_form)
    return handle_content_type(data)


def _handle_avatar_update(user, avatar_form):
    if avatar_form.validate_on_submit():
        _file = request.files['avatar']
        coordinates = (avatar_form.x1.data, avatar_form.y1.data,
                       avatar_form.x2.data, avatar_form.y2.data)
        prefix = time.time()
        _file.filename = "%s_avatar.png" % prefix
        container = "user_%s" % user.id
        uploader.upload_file(_file,
                             container=container,
                             coordinates=coordinates)
        # Delete previous avatar from storage
        if user.info.get('avatar'):
            uploader.delete_file(user.info['avatar'], container)
        upload_method = current_app.config.get('UPLOAD_METHOD')
        avatar_url = get_avatar_url(upload_method,
                                    _file.filename, container)
        user.info = {'avatar': _file.filename,
                     'container': container,
                     'avatar_url': avatar_url}
        user_repo.update(user)
        cached_users.delete_user_summary(user.name)
        flash(gettext('Your avatar has been updated! It may \
                      take some minutes to refresh...'), 'success')
        return True
    else:
        flash("You have to provide an image file to update your avatar", "error")
        return False


def _handle_profile_update(user, update_form):
    acc_conf_dis = current_app.config.get('ACCOUNT_CONFIRMATION_DISABLED')
    if update_form.validate_on_submit():
        user.id = update_form.id.data
        user.fullname = update_form.fullname.data
        user.name = update_form.name.data
        if (user.email_addr != update_form.email_addr.data and
                acc_conf_dis is False):
            user.valid_email = False
            user.newsletter_prompted = False
            account = dict(fullname=update_form.fullname.data,
                           name=update_form.name.data,
                           email_addr=update_form.email_addr.data)
            confirm_url = get_email_confirmation_url(account)
            subject = ('You have updated your email in %s! Verify it'
                       % current_app.config.get('BRAND'))
            msg = dict(subject=subject,
                       recipients=[update_form.email_addr.data],
                       body=render_template(
                           '/account/email/validate_email.md',
                           user=account, confirm_url=confirm_url))
            msg['html'] = markdown(msg['body'])
            mail_queue.enqueue(send_mail, msg)
            user.confirmation_email_sent = True
            fls = gettext('An email has been sent to verify your \
                          new email: %s. Once you verify it, it will \
                          be updated.' % account['email_addr'])
            flash(fls, 'info')
            return True
        if acc_conf_dis:
            user.email_addr = update_form.email_addr.data
        user.privacy_mode = update_form.privacy_mode.data
        user.locale = update_form.locale.data
        user.subscribed = update_form.subscribed.data
        user_repo.update(user)
        cached_users.delete_user_summary(user.name)
        flash(gettext('Your profile has been updated!'), 'success')
        return True
    else:
        flash(gettext('Please correct the errors'), 'error')
        return False


def _handle_password_update(user, password_form):
    if password_form.validate_on_submit():
        user = user_repo.get(user.id)
        if user.check_password(password_form.current_password.data):
            user.set_password(password_form.new_password.data)
            user_repo.update(user)
            flash(gettext('Yay, you changed your password succesfully!'),
                  'success')
            return True
        else:
            msg = gettext("Your current password doesn't match the "
                          "one in our records")
            flash(msg, 'error')
            return False
    else:
        flash(gettext('Please correct the errors'), 'error')
        return False


def _handle_external_services_update(user, update_form):
    del update_form.locale
    del update_form.email_addr
    del update_form.fullname
    del update_form.name
    if update_form.validate():
        user.ckan_api = update_form.ckan_api.data or None
        user_repo.update(user)
        cached_users.delete_user_summary(user.name)
        flash(gettext('Your profile has been updated!'), 'success')
        return True
    else:
        flash(gettext('Please correct the errors'), 'error')
        return False


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
        timeout = current_app.config.get('ACCOUNT_LINK_EXPIRATION', 3600)
        userdict = signer.loads(key, max_age=timeout, salt='password-reset')
    except BadData:
        abort(403)
    username = userdict.get('user')
    if not username or not userdict.get('password'):
        abort(403)
    user = user_repo.get_by_name(username)
    if user.passwd_hash != userdict.get('password'):
        abort(403)
    form = ChangePasswordForm(request.body)
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        user_repo.update(user)
        flash(gettext('You reset your password successfully!'), 'success')
        return _sign_in_user(user)
    if request.method == 'POST' and not form.validate():
        flash(gettext('Please correct the errors'), 'error')
    response = dict(template='/account/password_reset.html', form=form)
    return handle_content_type(response)


@blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Request a forgotten password for a user.

    Returns a Jinja2 template.

    """
    form = ForgotPasswordForm(request.body)
    if form.validate_on_submit():
        user = user_repo.get_by(email_addr=form.email_addr.data)
        if user and user.email_addr:
            msg = dict(subject='Account Recovery',
                       recipients=[user.email_addr])
            if user.twitter_user_id:
                msg['body'] = render_template(
                    '/account/email/forgot_password_openid.md',
                    user=user, account_name='Twitter')
                msg['html'] = render_template(
                    '/account/email/forgot_password_openid.html',
                    user=user, account_name='Twitter')
            elif user.facebook_user_id:
                msg['body'] = render_template(
                    '/account/email/forgot_password_openid.md',
                    user=user, account_name='Facebook')
                msg['html'] = render_template(
                    '/account/email/forgot_password_openid.html',
                    user=user, account_name='Facebook')
            elif user.google_user_id:
                msg['body'] = render_template(
                    '/account/email/forgot_password_openid.md',
                    user=user, account_name='Google')
                msg['html'] = render_template(
                    '/account/email/forgot_password_openid.html',
                    user=user, account_name='Google')
            else:
                userdict = {'user': user.name, 'password': user.passwd_hash}
                key = signer.dumps(userdict, salt='password-reset')
                recovery_url = url_for('.reset_password',
                                       key=key, _external=True)
                msg['body'] = render_template(
                    '/account/email/forgot_password.md',
                    user=user, recovery_url=recovery_url)
                msg['html'] = render_template(
                    '/account/email/forgot_password.html',
                    user=user, recovery_url=recovery_url)
            mail_queue.enqueue(send_mail, msg)
            flash(gettext("We've send you an email with account "
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
    data = dict(template='/account/password_forgot.html',
                form=form)
    return handle_content_type(data)


@blueprint.route('/<name>/resetapikey', methods=['GET', 'POST'])
@login_required
def reset_api_key(name):
    """
    Reset API-KEY for user.

    Returns a Jinja2 template.

    """
    if request.method == 'POST':
        user = user_repo.get_by_name(name)
        if not user:
            return abort(404)
        ensure_authorized_to('update', user)
        user.api_key = model.make_uuid()
        user_repo.update(user)
        cached_users.delete_user_summary(user.name)
        msg = gettext('New API-KEY generated')
        flash(msg, 'success')
        return redirect_content_type(url_for('account.profile', name=name))
    else:
        csrf = dict(form=dict(csrf=generate_csrf()))
        return jsonify(csrf)
