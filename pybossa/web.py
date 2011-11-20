import logging

from flask import request, g, render_template, abort, flash

from pybossa.core import app
import pybossa.model as model

logger = logging.getLogger('pybossa')


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
def inject_project_vars():
    return dict(title = app.config['TITLE'], copyright = app.config['COPYRIGHT'])


@app.route('/')
def home():
    return render_template('/home/index.html')

@app.route('/faq')
def faq():
    return render_template('/home/faq.html')

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config.get('DEBUG', True))

