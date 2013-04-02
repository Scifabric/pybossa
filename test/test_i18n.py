from helper import web
from base import model, db, Fixtures


class TestI18n(web.Helper):
    def setUp(self):
        super(TestI18n, self).setUp()
        Fixtures.create()

    # Tests

    def test_00_i18n_anonymous(self):
        """Test i18n anonymous works"""
        # First default 'en' locale
        with self.app as c:
            err_msg = "The page should be in English"
            res = c.get('/', headers=[('Accept-Language', 'en')])
            assert "Community" in res.data, err_msg
        # Second with 'es' locale
        with self.app as c:
            err_msg = "The page should be in Spanish"
            res = c.get('/', headers=[('Accept-Language', 'es')])
            assert "Comunidad" in res.data, err_msg

    def test_01_i18n_authenticated(self):
        """Test i18n as an authenticated user works"""
        with self.app as c:
            # First default 'en' locale
            err_msg = "The page should be in English"
            res = c.get('/', follow_redirects=True)
            assert "Community" in res.data, err_msg
            self.register()
            self.signin()
            # After signing in it should be in English
            err_msg = "The page should be in English"
            res = c.get('/', follow_redirects=True)
            assert "Community" in res.data, err_msg

            # Change it to Spanish
            user = db.session.query(model.User).filter_by(name='johndoe').first()
            user.locale = 'es'
            db.session.add(user)
            db.session.commit()

            res = c.get('/', follow_redirects=True)
            err_msg = "The page should be in Spanish"
            assert "Comunidad" in res.data, err_msg
            # Sign out should revert it to English
            self.signout()
            err_msg = "The page should be in English"
            res = c.get('/', follow_redirects=True)
            assert "Community" in res.data, err_msg
