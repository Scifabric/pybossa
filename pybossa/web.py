import logging

from flask import request, g, render_template, abort

from pybossa.core import app

logger = logging.getLogger('pybossa')


@app.route('/')
def home():
    return render_template('/home/index.html')

@app.route('/faq')
def home():
    return render_template('/home/faq.html')

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config.get('DEBUG', True))

