from base import web, model, Fixtures


class TestAuthentication:
    @classmethod
    def setup_class(cls):
        cls.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    def test_api_authenticate(self):
        """Test AUTHENTICATION works"""
        res = self.app.get('/?api_key=%s' % Fixtures.api_key)
        assert 'checkpoint::logged-in::tester' in res.data, res.data
