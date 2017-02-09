import json
from helper import web
from default import with_context
from mock import patch
from factories import ProjectFactory
from default import Test, db
from pybossa.repositories import ProjectRepository

class TestCoowners(web.Helper):

    def setup(self):
        super(TestCoowners, self).setUp()
        self.project_repo = ProjectRepository(db)

    @with_context
    def test_00_admin_and_owner_can_access_coowners_page(self):
        """Test admin and owner can access coowners page"""
        self.register()
        self.signin()
        self.signout()
        self.register(name="John2", email="john2@john.com",
                      password="passwd")
        self.signout()
        self.signin()
        res = self.app.get("/admin/users/addsubadmin/2", follow_redirects=True)
        self.signout()
        self.signin(email="john2@john.com", password="passwd")
        self.new_project()

        res = self.app.get('/project/sampleapp/coowners', follow_redirects=True)
        assert "Manage Co-owners" in res.data, res.data

        self.signout()
        self.signin()

        res = self.app.get('/project/sampleapp/coowners', follow_redirects=True)
        assert "Manage Co-owners" in res.data, res.data

    @with_context
    def test_01_admin_and_owner_add_del_coowner(self):
        """Test admin and owner can add/del a subadmin to coowners"""
        self.register()
        self.signin()
        self.signout()
        self.register(name="John2", email="john2@john.com",
                      password="passwd")
        self.register(name="John3", email="john3@john.com",
                      password="passwd")
        self.signout()
        self.signin()
        res = self.app.get("/admin/users/addsubadmin/2", follow_redirects=True)
        res = self.app.get("/admin/users/addsubadmin/3", follow_redirects=True)
        self.signout()
        self.signin(email="john2@john.com", password="passwd")
        self.new_project()

        res = self.app.get('/project/sampleapp/addcoowner/3', follow_redirects=True)
        assert "John3" in res.data, res.data

        res = self.app.get('/project/sampleapp/delcoowner/3', follow_redirects=True)
        assert "John3" not in res.data, res.data

        self.signout()
        self.signin()

        res = self.app.get('/project/sampleapp/addcoowner/3', follow_redirects=True)
        assert "John3" in res.data, res.data

        res = self.app.get('/project/sampleapp/delcoowner/3', follow_redirects=True)
        assert "John3" not in res.data, res.data

    @with_context
    def test_02_nonadmin_notowner_authenticated_user_cannot_add_del_coowners(self):
        """Test non admin/not an owner authenticated user cannot add/del coowners to a project"""
        self.register()
        self.signin()
        self.signout()
        self.register(name="John2", email="john2@john.com",
                      password="passwd")
        self.register(name="John3", email="john3@john.com",
                      password="passwd")
        self.signout()
        self.signin()
        self.new_project()
        res = self.app.get("/admin/users/addsubadmin/2", follow_redirects=True)
        res = self.app.get('/project/sampleapp/addcoowner/2', follow_redirects=True)
        self.signout()
        self.signin(email="john3@john.com", password="passwd")

        res = self.app.get('/project/sampleapp/addcoowner/3', follow_redirects=True)
        res = self.app.get('/project/sampleapp/delcoowner/2', follow_redirects=True)

        self.signout()
        self.signin()

        res = self.app.get('/project/sampleapp/coowners', follow_redirects=True)
        assert "John2" in res.data, res.data
        assert "John3" not in res.data, res.data
            
