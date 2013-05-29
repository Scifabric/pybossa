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
from flaskext.login import login_user, current_user

import pybossa.model as model
from pybossa.core import db
from pybossa.util import Twitter, get_user_signup_method
# Required to access the config parameters outside a
# context as we are using Flask 0.8
# See http://goo.gl/tbhgF for more info
from pybossa.core import app

# This blueprint will be activated in web.py
# if the TWITTER CONSUMER KEY and SECRET
# are available
blueprint = Blueprint('twitter', __name__)
twitter = Twitter(app.config['TWITTER_CONSUMER_KEY'],
                  app.config['TWITTER_CONSUMER_SECRET'])


@blueprint.route('/', methods=['GET', 'POST'])
def login():
    return twitter.oauth.authorize(callback=url_for('.oauth_authorized',
                                                    next=request.args.get("next")))


@twitter.oauth.tokengetter
def get_twitter_token():
    if current_user.is_anonymous():
        return None
    else:
        return((current_user.info['twitter_token']['oauth_token'],
               current_user.info['twitter_token']['oauth_token_secret']))


def manage_user(access_token, user_data, next_url):
    """Manage the user after signin"""
    # Twitter API does not provide a way
    # to get the e-mail so we will ask for it
    # only the first time
    user = db.session.query(model.User)\
             .filter_by(twitter_user_id=user_data['user_id'])\
             .first()

    if user is not None:
        return user

    twitter_token = dict(oauth_token=access_token['oauth_token'],
                         oauth_token_secret=access_token['oauth_token_secret'])
    info = dict(twitter_token=twitter_token)
    user = db.session.query(model.User)\
        .filter_by(name=user_data['screen_name'])\
        .first()

    if user is not None:
        return None
    user = model.User(fullname=user_data['screen_name'],
                      name=user_data['screen_name'],
                      email_addr=user_data['screen_name'],
                      twitter_user_id=user_data['user_id'],
                      info=info)
    db.session.add(user)
    db.session.commit()
    return user


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

    access_token = dict(oauth_token=resp['oauth_token'],
                        oauth_token_secret=resp['oauth_token_secret'])

    user_data = dict(screen_name=resp['screen_name'],
                     user_id=resp['user_id'])

    user = manage_user(access_token, user_data, next_url)

    if user is None:
        user = db.session.query(model.User)\
                 .filter_by(name=user_data['screen_name'])\
                 .first()
        msg, method = get_user_signup_method(user)
        flash(msg, 'info')
        if method == 'local':
            return redirect(url_for('account.forgot_password'))
        else:
            return redirect(url_for('account.signin'))

    first_login = False
    request_email = False
    login_user(user, remember=True)
    flash("Welcome back %s" % user.fullname, 'success')
    if (user.email_addr == user.name):
        request_email = True
    if not request_email:
        return redirect(next_url)
    if first_login:
        flash("This is your first login, please add a valid e-mail")
    else:
        flash("Please update your e-mail address in your profile page")
    return redirect(url_for('account.update_profile'))

