from base import web, model, db, Fixtures


class TestAdmin:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()

    def tearDown(self):
        db.session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    def register(self, method="POST", fullname="John Doe", username="johndoe",
                 password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and sign in a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        if method == "POST":
            return self.app.post('/account/register',
                                 data={
                                     'fullname': fullname,
                                     'username': username,
                                     'email_addr': email,
                                     'password': password,
                                     'confirm': password2},
                                 follow_redirects=True)
        else:
            return self.app.get('/account/register', follow_redirects=True)

    def signin(self, method="POST", email="johndoe@example.com", password="p4ssw0rd",
               next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next is not None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url, data={'email': email,
                                            'password': password},
                                 follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects=True)

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
