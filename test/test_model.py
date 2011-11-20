import pybossa.web as web
import pybossa.model as model

class TestModel:
    def test_01(self):
        dburi = web.app.config['SQLALCHEMY_DATABASE_URI']
        engine = model.create_engine(dburi)
        model.Base.metadata.drop_all(bind=engine)
        model.Base.metadata.create_all(bind=engine)
        model.set_engine(engine)
        app = model.App(name=u'My New App', short_name=u'my-new-app')
        model.Session.add(app)
        model.Session.commit()
        app_id = app.id 

        model.Session.remove()
        app = model.Session.query(model.App).get(app_id)
        assert app.name == u'My New App'

