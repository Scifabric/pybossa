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
from markdown import markdown
import json

from flask import Blueprint, request, url_for, flash, redirect, session, abort
from flask import render_template, current_app
from flaskext.login import login_required, login_user, logout_user, current_user
from flask.ext.mail import Message
from flaskext.wtf import Form, TextField, PasswordField, validators, \
        ValidationError, IntegerField, HiddenInput, SelectField

from flaskext.babel import lazy_gettext
from sqlalchemy.sql import func, text
import pybossa.model as model
from pybossa.model import User
from pybossa.core import db, signer, mail, cache, get_locale
from pybossa.util import Unique
from pybossa.util import Pagination
from pybossa.util import Twitter
from pybossa.util import Facebook
from pybossa.util import get_user_signup_method
from pybossa.cache import users as cached_users


blueprint = Blueprint('account', __name__)


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
@cache.cached(timeout=50)
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
                           total=count,
                           title="Community", pagination=pagination)


class LoginForm(Form):
    email = TextField(lazy_gettext('E-mail'),
                      [validators.Required(
                          message=lazy_gettext("The e-mail is required"))])

    password = PasswordField(lazy_gettext('Password'),
                             [validators.Required(
                                 message=lazy_gettext("You must provide a password"))])


@blueprint.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        email = form.email.data
        user = model.User.query.filter_by(email_addr=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            msg_1 = lazy_gettext("Welcome back") + " " + user.fullname
            flash(msg_1, 'success')
            return redirect(request.args.get("next") or url_for("home"))
        elif user:
            msg, method = get_user_signup_method(user)
            if method == 'local':
                msg = lazy_gettext("Ooops, Incorrect email/password")
                flash(msg, 'error')
            else:
                flash(msg, 'info')
        else:
            msg = lazy_gettext("Ooops, we didn't find you in the system, \
                               did you sign in?")
            flash(msg, 'info')

    if request.method == 'POST' and not form.validate():
        flash(lazy_gettext('Please correct the errors'), 'error')
    auth = {'twitter': False, 'facebook': False, 'google': False}
    if current_user.is_anonymous():
        # If Twitter is enabled in config, show the Twitter Sign in button
        if ('twitter' in current_app.blueprints):
            auth['twitter'] = True
        if ('facebook' in current_app.blueprints):
            auth['facebook'] = True
        if ('google' in current_app.blueprints):
            auth['google'] = True
        return render_template('account/signin.html',
                               title="Sign in",
                               form=form, auth=auth,
                               next=request.args.get('next'))
    else:
        # User already signed in, so redirect to home page
        return redirect(url_for("home"))


@blueprint.route('/signout')
def signout():
    logout_user()
    flash(lazy_gettext('You are now signed out'), 'success')
    return redirect(url_for('home'))


class RegisterForm(Form):
    err_msg = lazy_gettext("Full name must be between 3 and 35 characters long")
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=35, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and 35 characters long")
    err_msg_2 = lazy_gettext("The user name is already taken")
    username = TextField(lazy_gettext('User name'),
                         [validators.Length(min=3, max=35, message=err_msg),
                          Unique(db.session, model.User,
                                 model.User.name, err_msg_2)])

    err_msg = lazy_gettext("Email must be between 3 and 35 characters long")
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = TextField(lazy_gettext('Email Address'),
                           [validators.Length(min=3, max=35, message=err_msg),
                            validators.Email(),
                            Unique(db.session, model.User,
                                   model.User.email_addr, err_msg_2)])

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    password = PasswordField(lazy_gettext('New Password'),
                             [validators.Required(err_msg),
                              validators.EqualTo('confirm', err_msg_2)])

    confirm = PasswordField(lazy_gettext('Repeat Password'))


class UpdateProfileForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())

    err_msg = lazy_gettext("Full name must be between 3 and 35 characters long")
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=35, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and 35 characters long")
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('User name'),
                     [validators.Length(min=3, max=35, message=err_msg),
                      Unique(db.session, model.User, model.User.name,
                             err_msg_2)])

    err_msg = lazy_gettext("Email must be between 3 and 35 characters long")
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = TextField(lazy_gettext('Email Address'),
                           [validators.Length(min=3, max=35, message=err_msg),
                            validators.Email(),
                            Unique(db.session, model.User,
                                   model.User.email_addr, err_msg_2)])

    locale = SelectField(lazy_gettext('Default Language'))

    def set_locales(self, locales):
        """Fill the locale.choices"""
        choices = []
        for locale in locales:
            if locale == 'en':
                lang = lazy_gettext("English")
            if locale == 'es':
                lang = lazy_gettext("Spanish")
            choices.append((locale, lang))
        self.locale.choices = choices


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # TODO: re-enable csrf
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        account = model.User(fullname=form.fullname.data,
                             name=form.username.data,
                             email_addr=form.email_addr.data)
        account.set_password(form.password.data)
        account.locale = get_locale()
        db.session.add(account)
        db.session.commit()
        login_user(account, remember=True)
        flash(lazy_gettext('Thanks for signing-up'), 'success')
        return redirect(url_for('home'))
    if request.method == 'POST' and not form.validate():
        flash(lazy_gettext('Please correct the errors'), 'error')
    return render_template('account/register.html',
                           title=lazy_gettext("Register"), form=form)


@blueprint.route('/profile', methods=['GET'])
@login_required
def profile():
    user = db.session.query(model.User).get(current_user.id)

    sql = text('''
               SELECT app.name, app.short_name, app.info, COUNT(*) as n_task_runs
               FROM task_run JOIN app ON
               (task_run.app_id=app.id) WHERE task_run.user_id=:user_id
               GROUP BY app.name, app.short_name, app.info
               ORDER BY n_task_runs DESC;''')

    # results will have the following format (app.name, app.short_name, n_task_runs)
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

    user.total = db.session.query(model.User).count()
    return render_template('account/profile.html', title=lazy_gettext("Profile"),
                           apps_contrib=apps_contrib,
                           user=user)


@blueprint.route('/profile/applications')
@login_required
def applications():
    user = User.query.get_or_404(current_user.id)
    apps_published = []
    apps_draft = []

    sql = text('''
               SELECT app.name, app.short_name, app.description,
               app.info, count(task.app_id) as n_tasks
               FROM app LEFT OUTER JOIN task ON (task.app_id=app.id)
               WHERE app.owner_id=:user_id GROUP BY app.name, app.short_name,
               app.description,
               app.info;''')

    results = db.engine.execute(sql, user_id=user.id)
    for row in results:
        app = dict(name=row.name, short_name=row.short_name,
                   description=row.description,
                   info=json.loads(row.info), n_tasks=row.n_tasks,
                  )
        if app['n_tasks'] > 0:
            apps_published.append(app)
        else:
            apps_draft.append(app)

    return render_template('account/applications.html',
                           title=lazy_gettext("Applications"),
                           apps_published=apps_published,
                           apps_draft=apps_draft)

@blueprint.route('/profile/settings')
@login_required
def settings():
    #user = User.query.get_or_404(current_user.id)
    user, apps, apps_created = cached_users.get_user_summary(current_user.name)
    title = "User: %s &middot; Settings" % user['fullname']
    return render_template('account/settings.html',
                           title=title,
                           user=user)

@blueprint.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm(obj=current_user)
    form.set_locales(current_app.config['LOCALES'])
    form.populate_obj(current_user)
    if request.method == 'GET':
        title_msg = "Update your profile: %s" % current_user.fullname
        return render_template('account/update.html',
                               title=title_msg,
                               form=form)
    else:
        form = UpdateProfileForm(request.form)
        form.set_locales(current_app.config['LOCALES'])
        if form.validate():
            new_profile = model.User(id=form.id.data,
                                     fullname=form.fullname.data,
                                     name=form.name.data,
                                     email_addr=form.email_addr.data,
                                     locale=form.locale.data)
            db.session.query(model.User)\
              .filter(model.User.id == current_user.id)\
              .first()
            db.session.merge(new_profile)
            db.session.commit()
            flash(lazy_gettext('Your profile has been updated!'), 'success')
            return redirect(url_for('.profile'))
        else:
            flash(lazy_gettext('Please correct the errors'), 'error')
            title_msg = 'Update your profile: %s' % current_user.fullname
            return render_template('/account/update.html', form=form,
                                   title=title_msg)


class ChangePasswordForm(Form):
    current_password = PasswordField(lazy_gettext('Old Password'))

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New Password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat Password'))


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
            flash(lazy_gettext('Yay, you changed your password succesfully!'), 'success')
            return redirect(url_for('.profile'))
        else:
            msg = lazy_gettext("Your current password doesn't match the one in our records")
            flash(msg, 'error')
    if request.method == 'POST' and not form.validate():
        flash(lazy_gettext('Please correct the errors'), 'error')
    return render_template('/account/password.html', form=form)


class ResetPasswordForm(Form):
    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New Password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat Password'))


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
        flash(lazy_gettext('You reset your password successfully!'), 'success')
        return redirect(url_for('.profile'))
    if request.method == 'POST' and not form.validate():
        flash(lazy_gettext('Please correct the errors'), 'error')
    return render_template('/account/password_reset.html', form=form)


class ForgotPasswordForm(Form):
    err_msg = lazy_gettext("Email must be between 3 and 35 characters long")
    email_addr = TextField(lazy_gettext('Email Address'),
                           [validators.Length(min=3, max=35, message=err_msg),
                            validators.Email()])


@blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm(request.form)
    if form.validate_on_submit():
        user = model.User.query\
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
                key = signer.dumps(userdict, salt='password-reset')
                recovery_url = url_for('.reset_password',
                                       key=key, _external=True)
                msg.body = render_template(
                    '/account/email/forgot_password.md',
                    user=user, recovery_url=recovery_url)
            msg.html = markdown(msg.body)
            mail.send(msg)
            flash(lazy_gettext("We've send you email with account recovery instructions!"),
                  'success')
        else:
            flash(lazy_gettext("We don't have this email in our records. You may have"
                  " signed up with a different email or used Twitter, "
                  "Facebook, or Google to sign-in"), 'error')
    if request.method == 'POST' and not form.validate():
        flash(lazy_gettext('Something went wrong, please correct the errors on the '
              'form'), 'error')
    return render_template('/account/password_forgot.html', form=form)


@blueprint.route('/profile/resetapikey', methods=['GET', 'POST'])
@login_required
def reset_api_key():
    """Reset API-KEY for user"""
    if current_user.is_authenticated():
        title = "User: %s &middot; Settings - Reset API KEY" % current_user.fullname
        if request.method == 'GET':
            return render_template('account/reset-api-key.html',
                                   title=title)
        else:
            user = db.session.query(model.User).get(current_user.id)
            user.api_key = model.make_uuid()
            db.session.commit()
            msg = lazy_gettext('New API-KEY generated')
            flash(msg, 'success')
            return redirect(url_for('account.settings'))
    else:
        return abort(403)


@blueprint.route('/<name>/')
def public_profile(name):
    """Render the public user profile"""
    user, apps, apps_created = cached_users.get_user_summary(name)
    if user:
        title = "%s &middot; User Profile" % user['fullname']
        return render_template('/account/public_profile.html',
                               title=title,
                               user=user,
                               apps=apps,
                               apps_created=apps_created)
    else:
        abort(404)
