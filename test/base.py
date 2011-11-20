import os

import pybossa.web as web
import pybossa.model as model

_here = os.path.dirname(__file__)
web.app.config['TESTING'] = True
dburi = 'sqlite:///%s/test.db' % _here
print dburi
web.app.config['SQLALCHEMY_DATABASE_URI'] = dburi
engine = model.create_engine(dburi)
model.set_engine(engine)

