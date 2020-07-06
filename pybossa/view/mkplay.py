# -*- coding: utf8 -*-
# This file is part of myKaarma.
#


"""myKaarma view for PYBOSSA."""
from flask import Blueprint, request, url_for, flash, redirect, session, current_app
from flask import abort
from flask_login import login_user, current_user
from flask_oauthlib.client import OAuthException

import base64
import hashlib

from flask import Flask
from flask_saml2.exceptions import CannotHandleAssertion

from flask_saml2.sp import ServiceProvider

from tests.sp.base import CERTIFICATE, PRIVATE_KEY
from pybossa.extensions import csrf
from pybossa.core import mkplay, user_repo, newsletter
from pybossa.model.user import User
from pybossa.util import get_user_signup_method, username_from_full_name
from pybossa.util import url_for_app_type

import requests
from flask_saml2.sp.views import (
    AssertionConsumer, CannotHandleAssertionView, Login, LoginIdP, Logout,
    Metadata, SingleLogout)



class ExampleServiceProvider(ServiceProvider):
    def get_logout_return_url(self):
        #return url_for('index', _external=True)
        return url_for('mkplay.login', _external=True)
        #return "http://localhost:5000/"

    def get_default_login_return_url(self):
        return url_for('mkplay.login', _external=True)
        #return "http://localhost:5000/"


sp = ExampleServiceProvider()

blueprint = sp.create_blueprint()
csrf.exempt(blueprint)


@blueprint.route('/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    print("inside login")
    """Login with myKaarma."""
    if not current_app.config.get('LDAP_HOST', False):
       
        print("in index function")
        if sp.is_user_logged_in():
            print("in if user logged in sp")
            auth_data = sp.get_auth_data_in_session()
            print(auth_data,"authdata")
            message = f'''
            <p>You are logged in as <strong>{auth_data.nameid}</strong>.
            The IdP sent back the following attributes:<p>
            '''
            attrs = '<dl>{}</dl>'.format(''.join(
                f'<dt>{attr}</dt><dd>{value}</dd>'
                for attr, value in auth_data.attributes.items()))
            user_data = {}
            user_data['id'] = auth_data.attributes["UserUUID"]
            user_data['name'] = auth_data.attributes["name"]
            user_data['email'] = auth_data.attributes["email"]
            print("USERDATA",user_data)
            # logout_url = url_for('mkplay.logout')
            # logout = f'<form action="{logout_url}" method="POST"><input type="submit" value="Log out"></form>'

            # return message + attrs + logout
            
            user = manage_user(user_data)
            next_url = request.args.get('next') or url_for_app_type('home.home')
            return manage_user_login(user, user_data, next_url)
        else:
            print("in else user logged in")
            message = '<p>You are logged out.</p>'

            login_url = url_for('mkplay.login_mkplay')
            print("LOGIN URL IT IS GETTING",login_url)
            link = f'<p><a href="{login_url}">Log in to continue</a></p>'
            return message + link
    else:
        return abort(404)
    

@blueprint.errorhandler(404)
@blueprint.errorhandler(400)
def _handle_api_error(ex):
    print(ex)
    


def manage_user(user_data):
    """Manage the user after signin"""
    # We have to store the oauth_token in the session to get the USER fields

    user = user_repo.get_by(mkplay_user_id=user_data['id'])
    #
    # user =None

    #user = user_repo.get_by(email_addr=user_data['email'])
    #google_token = dict(oauth_token=access_token)
    print("user", user)
    # user never signed on
    if user is None:
        #info = dict(google_token=google_token)
        #name = username_from_full_name(user_data['name'])
        #user = user_repo.get_by_name(name)

        userByEmail = user_repo.get_by(email_addr=user_data['email'])
        #print("email is ", email)

        if (userByEmail is None):
            print("INSIDE If")
            #name = username_from_full_name(user_data['name'])
            body = user_data['name']
            name = b"mkplay-" +  base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest())
            
            #user = user_repo.get_by_name(name)
            #name not unique
            #if(user is not None):

           
            user = User(fullname=user_data['name'],
                        name=name,
                        email_addr=user_data['email'],
                        mkplay_user_id=user_data['id'])
            user_repo.save(user)
            if newsletter.is_initialized():
                newsletter.subscribe_user(user)
            return user
        else:
            print(userByEmail.name,"username")
            print("usergenerated",username_from_full_name(user_data['name']))
            if (userByEmail.name == username_from_full_name(user_data['name']).decode('utf-8')):
                body = user_data['name']
                userByEmail.name = b"mkplay-" +  base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest())
            userByEmail.mkplay_user_id=user_data['id']
            user_repo.save(userByEmail)
            return userByEmail
    else:
        #user.info['mkplay_token'] = google_token
        # Update the name to fit with new paradigm to avoid UTF8 problems
        #if type(user.name) == str or ' ' in user.name:
        #    user.name = username_from_full_name(user.name).decode('utf-8')
        
        # if (user.name == username_from_full_name(user_data['name'])):
        #     body = user_data['name']
        #     user.name = b"mkplay-" +  base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest())
        user_repo.save(user)
        return user


def manage_user_login(user, user_data, next_url):
    """Manage user login."""
    if user is None:
        print("user is NONE")
        # Give a hint for the user
        user = user_repo.get_by(email_addr=user_data['email'])
        if user is None:
            name = username_from_full_name(user_data['name'])
            user = user_repo.get_by_name(name)
            print("user details")
        

        msg, method = get_user_signup_method(user)
        flash(msg, 'info')
        if method == 'local':
            return redirect(url_for_app_type('account.forgot_password',
                                            _hash_last_flash=True))
        else:
            return redirect(url_for_app_type('account.signin',
                                            _hash_last_flash=True))
        
    else:
        print("login user")
        login_user(user, remember=True)
        flash("Welcome back %s" % user.fullname, 'success')
        if user.newsletter_prompted is False and newsletter.is_initialized():
            return redirect(url_for_app_type('account.newsletter_subscribe',
                                             next=next_url,
                                             _hash_last_flash=True))
        return redirect(next_url)
