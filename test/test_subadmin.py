import json
from helper import web
from default import with_context
from mock import patch

class TestSubAdmin(web.Helper):

    @with_context
    def test_00_admin_can_access_subadmin_page(self):
        """Test admin accessing subadmin page works"""
        self.register()
        self.signin()
        res = self.app.get('/admin/subadminusers', follow_redirects=True)
        assert "Manage Subadmin Users" in res.data, res.data
