import pybossa.web as web
import pybossa.model as model

class TestModel:
    @classmethod
    def setup_class(self):
        dburi = web.app.config['SQLALCHEMY_DATABASE_URI']
        engine = model.create_engine(dburi)
        model.Base.metadata.drop_all(bind=engine)
        model.Base.metadata.create_all(bind=engine)
        model.set_engine(engine)

    def test_01(self):
        app = model.App(name=u'My New App', short_name=u'my-new-app')
        model.Session.add(app)
        model.Session.commit()
        app_id = app.id 

        model.Session.remove()
        app = model.Session.query(model.App).get(app_id)
        assert app.name == u'My New App'

    def test_user(self):
        user = model.User(name=u'test-user', email_addr=u'test@xyz.org')
        model.Session.add(user)
        model.Session.commit()
        user_id = user.id 

        model.Session.remove()
        user = model.User.by_name(u'test-user')
        assert user

        out = user.dictize()
        assert out['name'] == u'test-user'


