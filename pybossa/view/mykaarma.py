# -*- coding: utf8 -*-
# This file is part of myKaarma.
#


"""myKaarma view for PYBOSSA."""
from flask import Blueprint, request, url_for, flash, redirect, session, current_app
from flask import abort
from flask_login import login_user, current_user
from flask_oauthlib.client import OAuthException


from flask import Flask
from flask_saml2.exceptions import CannotHandleAssertion

from flask_saml2.sp import ServiceProvider


from pybossa.extensions import csrf
from pybossa.core import mykaarma, user_repo, newsletter
from pybossa.model.user import User
from pybossa.util import get_user_signup_method, get_mykaarma_username_from_full_name, username_from_full_name
from pybossa.util import url_for_app_type

import requests
from flask_saml2.sp.views import (
    AssertionConsumer, CannotHandleAssertionView, Login, LoginIdP, Logout,
    Metadata, SingleLogout)



class ExampleServiceProvider(ServiceProvider):
    def get_logout_return_url(self):
        return url_for('mykaarma.login', _external=True, _scheme='https')

    def get_default_login_return_url(self):
        return url_for('mykaarma.login', _external=True, _scheme='https')


sp = ExampleServiceProvider()

blueprint = sp.create_blueprint()
csrf.exempt(blueprint)


@blueprint.route('/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    """Login with myKaarma."""
    if not current_app.config.get('LDAP_HOST', False):
        if sp.is_user_logged_in():
            auth_data = sp.get_auth_data_in_session()

            """Add received data from idp to a user data dictionary"""
            user_data = {}
            user_data['id'] = auth_data.attributes["UserUUID"]
            user_data['name'] = auth_data.attributes["name"]
            user_data['email'] = auth_data.attributes["email"]

            """Find user details or create user with details"""
            user = manage_user(user_data)
            next_url = request.args.get('next') or url_for_app_type('home.home')
            return manage_user_login(user, user_data, next_url)
        else:
            return redirect(url_for('mykaarma.login_mykaarma',_scheme='https',_external=True), code=302)
    else:
        return abort(404)
    

@blueprint.errorhandler(404)
@blueprint.errorhandler(400)
def _handle_api_error(ex):
    print(ex)
    


def manage_user(user_data):
    """Manage the user after signin"""
    # We have to store the oauth_token in the session to get the USER fields

    user = user_repo.get_by(mykaarma_user_id=user_data['id'])
    # user never signed on
    if user is None:
        user_by_email = user_repo.get_by(email_addr=user_data['email'])

        if (user_by_email is None):

            """Generate 4 digit alphanumeric string with digits and lowercase characters"""
            name = get_mykaarma_username_from_full_name(user_data['name'])


            """check if already a user present with the same name, if yes, generate another random string"""
            user = user_repo.get_by_name(name)
            while(user is not None):
                name = get_mykaarma_username_from_full_name(user_data['name']) 
                user = user_repo.get_by_name(name)

            """add user"""
            user = User(fullname=user_data['name'],
                        name=name,
                        email_addr=user_data['email'],
                        mykaarma_user_id=user_data['id'])
            user_repo.save(user)
            if newsletter.is_initialized():
                newsletter.subscribe_user(user)
            return user
        else:
            return add_through_email(user_by_email,user_data)
    else:
        return user


def add_through_email(user_by_email,user_data):
    if (user_by_email.name == username_from_full_name(user_data['name']).decode('utf-8')):
        name = get_mykaarma_username_from_full_name(user_data['name']) 
        user = user_repo.get_by_name(name)
        while(user is not None):
            name = get_mykaarma_username_from_full_name(user_data['name'])
            user = user_repo.get_by_name(name)
        user_by_email.name = name
    user_by_email.mykaarma_user_id=user_data['id']
    user_repo.save(user_by_email)
    return user_by_email

def manage_user_login(user, user_data, next_url):
    """Manage user login."""
    if user is None:
        # Give a hint for the user
        user = user_repo.get_by(email_addr=user_data['email'])
        if user is None:
            name = username_from_full_name(user_data['name'])
            user = user_repo.get_by_name(name)
        msg, method = get_user_signup_method(user)
        flash(msg, 'info')
        if method == 'local':
            return redirect(url_for_app_type('account.forgot_password',
                                            _hash_last_flash=True))
        else:
            return redirect(url_for_app_type('account.signin',
                                            _hash_last_flash=True))
        
    else:
        login_user(user, remember=True)
        flash("Welcome back %s" % user.fullname, 'success')
        if user.newsletter_prompted is False and newsletter.is_initialized():
            return redirect(url_for_app_type('account.newsletter_subscribe',
                                             next=next_url,
                                             _hash_last_flash=True))
        return redirect(next_url)
