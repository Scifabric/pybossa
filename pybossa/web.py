import logging

from flask import request, g, render_template, abort, flash, redirect, session
from flaskext.login import login_user, logout_user, current_user

from pybossa.core import app, login_manager
import pybossa.model as model
from pybossa.api import blueprint as api

logger = logging.getLogger('pybossa')

# other views ...
app.register_blueprint(api, url_prefix='/api')

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
        current_user=current_user
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
    return render_template('/home/index.html')

@app.route('/faq')
def faq():
    return render_template('/home/faq.html')

@app.route('/login')
def login():
    '''Stub login (to be replaced asap) ...'''
    tester = model.User.by_name('tester')
    login_user(tester, remember=True)
    flash('You were logged in', 'success')
    return redirect('/')

@app.route('/logout')
def logout():
    logout_user()
    flash('You were logged out', 'success')
    return redirect('/')


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config.get('DEBUG', True))

