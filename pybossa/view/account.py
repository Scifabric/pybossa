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

from flask import Blueprint, request, url_for, flash, redirect
from flask import render_template
from flaskext.login import login_required, login_user, logout_user, current_user
from flaskext.wtf import Form, TextField, PasswordField, validators, ValidationError

import pybossa.model as model
from pybossa.util import Unique

blueprint = Blueprint('account', __name__)

@blueprint.route('/')
def index():
    accounts = model.Session.query(model.User).all()
    return render_template('account/index.html', accounts = accounts)
    
class LoginForm(Form):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        username = form.username.data
        user = model.User.by_name(username)
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back', 'success')
            return redirect(url_for('home'))
        else:
            flash('Incorrect email/password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid form', 'error')
    return render_template('account/login.html', form=form)


@blueprint.route('/logout')
def logout():
    logout_user()
    flash('You are now logged out', 'success')
    return redirect(url_for('home'))


class RegisterForm(Form):
    username = TextField('Username', [validators.Length(min=3, max=25)])
    email_addr = TextField('Email Address', [validators.Length(min=3, max=35),
                                        Unique(model.Session, model.User,
                                               model.User.email_addr)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # TODO: re-enable csrf
    form = RegisterForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        account = model.User(
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
    return render_template('account/register.html', form=form)

@blueprint.route('/profile', methods = ['GET', 'POST'])
@login_required
def profile():
    return render_template('account/profile.html')
