import json

import pybossa.web as web
import pybossa.model as model


class TestAPI:
    def setUp(self):
        web.app.config['TESTING'] = True
        self.app = web.app.test_client()
        dburi = web.app.config['SQLALCHEMY_DATABASE_URI']
        engine = model.create_engine(dburi)
        model.Base.metadata.drop_all(bind=engine)
        model.Base.metadata.create_all(bind=engine)

    def test_01(self):
        res = self.app.get('/api/project')
        # assert 'nothing' in res.data, res.data

    def test_02(self):
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project'
            )
        data = json.dumps(data)
        res = self.app.post('/api/project',
            data=data
        )
        out = model.Session.query(model.App).filter_by(name=name).one()
        assert out

