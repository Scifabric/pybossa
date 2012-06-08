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

from flask import Response, request, g, render_template, abort, flash, redirect, session
from flaskext.login import login_user, logout_user, current_user
from sqlalchemy.exc import UnboundExecutionError
from werkzeug.exceptions import *

import pybossa
from pybossa.core import app, login_manager
import pybossa.model as model
from pybossa.api import blueprint as api
from pybossa.view.account import blueprint as account
from pybossa.view.applications import blueprint as applications
from pybossa.view.stats import blueprint as stats

import random 

logger = logging.getLogger('pybossa')

# other views ...
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(applications, url_prefix='/app')
app.register_blueprint(stats, url_prefix='/stats')

# Enable Twitter if available
try:
    if (app.config['TWITTER_CONSUMER_KEY'] and app.config['TWITTER_CONSUMER_SECRET']):
        from pybossa.view.twitter import blueprint as twitter
        app.register_blueprint(twitter, url_prefix='/twitter')
except:
    print "Twitter singin disabled"

@app.before_request
def bind_db_engine():
    dburi = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if dburi:
        engine = model.create_engine(dburi)
        model.set_engine(engine)
    else:
        flash('You have not yet configured the database', 'error')

@app.before_request
def remove_db_session():
    model.Session.remove()

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
    return dict(
        brand = app.config['BRAND'],
        title = app.config['TITLE'],
        copyright = app.config['COPYRIGHT'],
        description = app.config['DESCRIPTION'],
        version = pybossa.__version__,
        current_user = current_user,
        apps =  model.Session.query(model.App).filter(model.App.hidden == 0)
        )

@login_manager.user_loader
def load_user(username):
    # HACK: this repetition is painful but seems that before_request not yet called
    # TODO: maybe time to use Flask-SQLAlchemy
    dburi = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    engine = model.create_engine(dburi)
    model.set_engine(engine)
    return model.Session.query(model.User).filter_by(name=username).first()

@app.before_request
def api_authentication():
    """ Attempt API authentication on a per-request basis. """
    apikey = request.args.get('api_key', None)
    from flask import _request_ctx_stack
    if 'Authorization' in request.headers:
        apikey = request.headers.get('Authorization')
    if apikey:
        dburi = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        engine = model.create_engine(dburi)
        model.set_engine(engine)
        user = model.Session.query(model.User).filter_by(api_key=apikey).first()
        ## HACK: 
        # login_user sets a session cookie which we really don't want.
        # login_user(user)
        if user:
            _request_ctx_stack.top.user = user

@app.route('/')
def home():
    try: # in case we have not set up database yet
        app_count = model.Session.query(model.App).filter(model.App.hidden == 0).count()
        task_count = model.Session.query(model.Task).count()
        taskrun_count = model.Session.query(model.TaskRun).count()
        user_count = model.Session.query(model.User).count()
        stats = {
            'app': app_count,
            'task': task_count,
            'taskrun': taskrun_count,
            'user': user_count
            }
        apps = model.Session.query(model.App).filter(model.App.hidden == 0).all()
        threeApps = False
        if (len(apps) > 0):
            if (len(apps) == 1 or len(apps) == 2):
                frontPageApps = apps
                tmp = model.App( name = "Your application", description = "Could be here!")
                frontPageApps.append(tmp)
            else:
                frontPageApps = []
                for i in range(0,3):
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
    if current_user.is_authenticated() and current_user.email_addr == "None":
        flash("Please update your e-mail address in your profile page, right now it is empty!")
    return render_template('/home/index.html', stats = stats, frontPageApps = frontPageApps, threeApps = threeApps)

@app.route("/about")
def about():
    """Render the about template"""
    return render_template("/home/about.html")

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config.get('DEBUG', True))

