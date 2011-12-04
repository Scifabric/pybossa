from base import web, model

class TestModel:
    @classmethod
    def setup_class(self):
        model.rebuild_db()

    def test_01(self):
        info = {
            'total': 150,
            'long_description': 'hello world'
            }
        app = model.App(
            name=u'My New App',
            short_name=u'my-new-app',
            info=info
            )
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

