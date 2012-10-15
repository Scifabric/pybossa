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

import logging
import json

from flask import Response, request, g, render_template,\
        abort, flash, redirect, session, url_for
from flaskext.login import login_user, logout_user, current_user
from sqlalchemy.exc import UnboundExecutionError
from werkzeug.exceptions import *

import pybossa
from pybossa.core import app, login_manager, db
import pybossa.model as model
from pybossa.api import blueprint as api
from pybossa.view.account import blueprint as account
from pybossa.view.applications import blueprint as applications
from pybossa.view.admin import blueprint as admin
from pybossa.view.stats import blueprint as stats

import random

logger = logging.getLogger('pybossa')

# other views ...
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(applications, url_prefix='/app')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(stats, url_prefix='/stats')


# Enable Twitter if available
try:
    if (app.config['TWITTER_CONSUMER_KEY'] and
            app.config['TWITTER_CONSUMER_SECRET']):
        from pybossa.view.twitter import blueprint as twitter
        app.register_blueprint(twitter, url_prefix='/twitter')
except:
    print "Twitter singin disabled"

# Enable Facebook if available
try:
    if (app.config['FACEBOOK_APP_ID'] and app.config['FACEBOOK_APP_SECRET']):
        from pybossa.view.facebook import blueprint as facebook
        app.register_blueprint(facebook, url_prefix='/facebook')
except Exception as inst:
    print type(inst)
    print inst.args
    print inst
    print "Facebook singin disabled"

# Enable Google if available
try:
    if (app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_SECRET']):
        from pybossa.view.google import blueprint as google 
        app.register_blueprint(google, url_prefix='/google')
except Exception as inst:
    print type(inst)
    print inst.args
    print inst
    print "Google singin disabled"



def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

#@app.errorhandler(401)
#@app.errorhandler(403)
#@app.errorhandler(404)
#@app.errorhandler(410)
#@app.errorhandler(500)
#def handle_exceptions(exc):
#    """
#    Re-format exceptions to JSON
#
#    :arg error: The exception object
#    :returns: The exception object in JSON format
#    """
#    output = {'status': exc.code,
#              'name': exc.name,
#              'description': exc.description
#             }
#    return json.dumps(output)


@app.context_processor
def global_template_context():
    if current_user.is_authenticated():
        if (current_user.email_addr == current_user.name or
                current_user.email_addr == "None"):
            flash("Please update your e-mail address in your profile page,"
                  " right now it is empty!", 'error')

    return dict(
        brand=app.config['BRAND'],
        title=app.config['TITLE'],
        copyright=app.config['COPYRIGHT'],
        description=app.config['DESCRIPTION'],
        terms_of_use=app.config['TERMSOFUSE'],
        data_use=app.config['DATAUSE'],
        version=pybossa.__version__,
        current_user=current_user,
        )


@login_manager.user_loader
def load_user(username):
    return db.session.query(model.User).filter_by(name=username).first()


@app.before_request
def api_authentication():
    """ Attempt API authentication on a per-request basis."""
    apikey = request.args.get('api_key', None)
    from flask import _request_ctx_stack
    if 'Authorization' in request.headers:
        apikey = request.headers.get('Authorization')
    if apikey:
        user = db.session.query(model.User).filter_by(api_key=apikey).first()
        ## HACK:
        # login_user sets a session cookie which we really don't want.
        # login_user(user)
        if user:
            _request_ctx_stack.top.user = user

@app.route('/')
def home():
    # in case we have not set up database yet
    try:
        app_count = db.session.query(model.App)\
                .filter(model.App.hidden == 0)\
                .count()
        task_count = db.session.query(model.Task).count()
        taskrun_count = db.session.query(model.TaskRun).count()
        user_count = db.session.query(model.User).count()
        stats = {
            'app': app_count,
            'task': task_count,
            'taskrun': taskrun_count,
            'user': user_count
            }

        featured = db.session.query(model.Featured).all()

        apps = []
        for f in featured:
            apps.append(db.session.query(model.App).get(f.app_id))

        threeApps = False
        if (len(apps) > 0):
            if (len(apps) == 1 or len(apps) == 2):
                frontPageApps = apps
                tmp = model.App(name="Your application",
                        description="Could be here!")
                frontPageApps.append(tmp)
            else:
                frontPageApps = []
                for i in range(0, 3):
                    app = random.choice(apps)
                    apps.pop(apps.index(app))
                    frontPageApps.append(app)
                    threeApps = True
        else:
            frontPageApps = []

    except UnboundExecutionError:
        stats = {
            'app': 0,
            'task': 0,
            'taskrun': 0,
            'user': 0
            }
    return render_template('/home/index.html', stats=stats,
            frontPageApps=frontPageApps, threeApps=threeApps)


@app.route("/about")
def about():
    """Render the about template"""
    return render_template("/home/about.html")

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    app.run(host=app.config['HOST'], port=app.config['PORT'],
            debug=app.config.get('DEBUG', True))
