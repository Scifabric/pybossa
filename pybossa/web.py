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

from flask import request, g, render_template, abort, flash, redirect, session
from flaskext.login import login_user, logout_user, current_user
from sqlalchemy.exc import UnboundExecutionError

from pybossa.core import app, login_manager
import pybossa.model as model
from pybossa.api import blueprint as api
from pybossa.view.account import blueprint as account

logger = logging.getLogger('pybossa')

# other views ...
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(account, url_prefix='/account')

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

@app.context_processor
def global_template_context():
    return dict(
        title = app.config['TITLE'],
        copyright = app.config['COPYRIGHT'],
        description = app.config['DESCRIPTION'],
        version = app.config['VERSION'],
        current_user = current_user,
        apps =  model.Session.query(model.App).filter(model.App.hidden == 0)
        )

@login_manager.user_loader
def load_user(userid):
    # HACK: this repetition is painful but seems that before_request not yet called
    # TODO: maybe time to use Flask-SQLAlchemy
    dburi = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    engine = model.create_engine(dburi)
    model.set_engine(engine)
    return model.Session.query(model.User).filter_by(name=userid).first()


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
    except UnboundExecutionError:
        stats = {
            'app': 0,
            'task': 0,
            'taskrun': 0,
            'user': 0
            }
    return render_template('/home/index.html', stats=stats)

@app.route('/faq')
def faq():
    return render_template('/home/faq.html')

@app.route('/flickrperson')
def flickrperson():
    return render_template('/flickrperson/example.html')

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config.get('DEBUG', True))

