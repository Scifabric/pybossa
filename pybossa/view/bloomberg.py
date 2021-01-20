# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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

from flask import Blueprint, request, flash, url_for, redirect, current_app, abort
from flask_babel import gettext
from pybossa.core import user_repo, csrf
from pybossa.view.account import _sign_in_user, create_account
from urlparse import urlparse
from pybossa.util import generate_bsso_account_notification
from pybossa.util import is_own_url_or_else, generate_password
from pybossa.jobs import send_mail
from pybossa.exc.repository import DBIntegrityError
from pybossa.data_access import data_access_levels
from onelogin.saml2.auth import OneLogin_Saml2_Auth

blueprint = Blueprint('bloomberg', __name__)


@blueprint.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():  # pragma: no cover
    """Login with Bloomberg."""
    if not current_app.config.get('BSSO_SETTINGS'):
        abort(404)
    if request.method == 'GET':
        return redirect_to_bloomberg_sso()
    elif request.method == 'POST':
        return handle_bloomberg_response()


def prepare_onelogin_request():
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        'query_string': request.query_string
    }


def redirect_to_bloomberg_sso():
    sso_settings = current_app.config.get('BSSO_SETTINGS')
    auth = OneLogin_Saml2_Auth(prepare_onelogin_request(), sso_settings)
    next_url = (is_own_url_or_else(request.args.get('next'), url_for('home.home')) or
                url_for('home.home'))
    return redirect(auth.login(return_to=next_url))


def handle_bloomberg_response():
    sso_settings = current_app.config.get('BSSO_SETTINGS')
    auth = OneLogin_Saml2_Auth(prepare_onelogin_request(), sso_settings)
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        # BSSO was unable to authenticate the user
        error_reason = auth.get_last_error_reason()
        current_app.logger.error('BSSO auth error(s): %s %s', errors, error_reason)
        flash(gettext('There was a problem during the sign in process.'), 'error')
        return redirect(url_for('home.home'))
    elif auth.is_authenticated:
        # User is authenticated on BSSO, load user from GIGwork API.
        attributes = auth.get_attributes()
        user = user_repo.get_by(email_addr=unicode(attributes['emailAddress'][0]).lower())
        if user is not None:
            # User is authenticated on BSSO and already has a GIGwork account.
            return _sign_in_user(user, next_url=request.form.get('RelayState'))
        else:
            # User is authenticated on BSSO, but does not yet have a GIGwork account, auto create one.
            current_app.logger.info('User authenticated via bsso but no account found. Attempting to create account for: %s', str(attributes))
            user_data = {}
            try:
                firm_id_to_type = current_app.config.get('FIRM_TO_TYPE', "")
                firm_id = int(attributes.get('firmId', [0])[0])
                data_access = ["L2"] if bool(data_access_levels) else ["L4"]
                user_type = firm_id_to_type.get(firm_id, "")
                user_data['fullname']    = attributes['firstName'][0] + " " + attributes['lastName'][0]
                user_data['email_addr']  = attributes['emailAddress'][0]
                user_data['name']        = attributes['username'][0]
                user_data['password']    = generate_password()
                user_data['admin']       = 'BSSO'
                user_data['data_access'] = data_access
                user_data['user_type'] = user_type
                create_account(user_data, auto_create=True)
                current_app.logger.info('Account created using BSSO info: %s', str(user_data))
                flash('A new account has been created for you using BSSO.')
                user = user_repo.get_by(email_addr=unicode(user_data['email_addr'].lower()))
                return _sign_in_user(user, next_url=request.form.get('RelayState'))
            except Exception as error:
                brand = current_app.config['BRAND']
                current_app.logger.exception('Auto-account creation error: %s, for user attributes: %s', error, attributes)
                flash(gettext('There was a problem signing you in. Please contact your {} administrator.'.format(brand)), 'error')
                return redirect(url_for('home.home'))
    else:
        # Failed to authenticate user on BSSO.
        current_app.logger.exception('BSSO login error')
        flash(gettext('We were unable authenticate and log you into an account. Please contact a Gigwork administrator.'), 'error')
        return redirect(url_for('home.home'))


