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

import pybossa.model as model
from pybossa.util import Unique
from pybossa.util import Twitter
# Required to access the config parameters outside a context as we are using Flask 0.8
# See http://goo.gl/tbhgF for more info
from pybossa.core import app

# This blueprint will be activated in web.py if the TWITTER CONSUMER KEY and SECRET
# are available
blueprint = Blueprint('twitter', __name__)
twitter = Twitter(app.config['TWITTER_CONSUMER_KEY'], app.config['TWITTER_CONSUMER_SECRET'])

@blueprint.route('/', methods=['GET','POST'])
def login():
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
        user = model.Session.query(model.User)\
                .filter_by(name=resp['screen_name']).first()
        if user is None:
            user = model.User(
                    fullname = resp['screen_name'],
                    name = resp['screen_name'],
                    email_addr = 'None',
                    twitter_user_id = resp['user_id'],
                    info = info 
                    )
            model.Session.add(user)
            model.Session.commit()
        else:
            flash(u'Sorry, there is already an account with the same user name.', 'error') 
            flash(u'You can create a new account and sign in', 'info')
            return redirect(url_for('account.register'))


    login_user(user, remember=True)
    flash("Welcome back %s" % user.fullname, 'success')
    if (user.email_addr == "None"): request_email = True

    if request_email:
        if first_login:
            flash("This is your first login, please add a valid e-mail")
        else:
            flash("Please update your e-mail address in your profile page")
        return redirect(url_for('account.update_profile'))

    return redirect(next_url)
