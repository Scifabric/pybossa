from helper import web
from base import model, db, Fixtures
from nose.tools import assert_equal
from bs4 import BeautifulSoup

class TestTeams(web.Helper):
    # Helper functions
    def new_team(self, method="POST",
                name="TeamTest",
                description="Team TestDescription",
                public=True,
                owner=1):

        ''' Test TEAM create team work'''
        if method == "POST":
            if public == True:
                return self.app.post('/team/new/',
                            data={
                                'name':        name,
                                'description': description,
                                'public':      public,
                                'owner':       owner
                                },
                                follow_redirects=True)
            else:
                return self.app.post('/team/new/',
                            data={
                                'name':        name,
                                'description': description,
                                'owner':       owner
                                },
                                follow_redirects=True)
        else:
            return self.app.get("/team/new/", follow_redirects=True)

    def delete_team(self, method="POST",
            name="TeamTest",
            description="Team TestDescription",
            public=True):
        ''' Test TEAM delete team work'''
        if method == "POST":
            return self.app.post("/team/%s/delete" % name,
                            follow_redirects=True)
        else:
            return self.app.get("/team/%s/delete" % name,
                            follow_redirects=True)

    def update_team(self, method="POST",
            name="TeamTest",
            new_name="Team Sample",
            new_description="Team Sample Description",
            new_public=True):
        ''' Test TEAM update team work'''
        if method == "POST":
            return self.app.post("/team/%s/update" % name,
                            data={
                                'name': 		new_name,
                                'description': 	new_description,
                                'public': 	new_public
                                },
				                follow_redirects=True)
        else:
            return self.app.get("/team/%s/update" % name,
                            follow_redirects=True)

    def test_00_team_index_anonymous(self):
        ''' Test 00 TEAM index page works as anonymous user'''
        res = self.app.get("/team", follow_redirects=True)

        err_msg = ("The anonymous user should not be able to access"
                  "but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in res.data, err_msg

    def test_01_team_index_admin(self):
        ''' Test 01 TEAM index page works as admin user'''
        self.register()
        res = self.app.get("/team", follow_redirects=True)

        err_msg = ("There would be a team page with at least "
                "a button My Teams:  %s" % res.data)

        assert "My Teams" in res.data, err_msg
        self.signout

    def test_02_team_index_authenticated(self):
        ''' Test 02 TEAM index page works as authenticated user'''
        self.register()
        self.signout()
        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        res = self.app.get("/team", follow_redirects=True)
        err_msg = ("There would be a team page with at least "
                "a button My Teams:  %s" % res.data)
        self.signout()

    def test_03_team_add_admin(self):
        ''' Test 03 TEAM create a team as admin'''
        self.register()

        res = self.app.get("/team/myteams", follow_redirects=True)
        err_msg = "There should be a button for Create Team"
        assert "Create new Team" in res.data, err_msg

        res = self.new_team(name="TestTeam")
        assert "Team created" in res.data, res
        self.signout

        team = db.session.query(model.Team).get(1)
        assert team.name == "TestTeam", "Team does not created"

    def test_04_team_add_authenticated(self):
        ''' Test 04 TEAM create a team as authenticated user'''
        self.register()
        self.signout()
        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        res = self.app.get("/team/myteams", follow_redirects=True)
        err_msg = "There should be a button for Create Team"
        assert "Create new Team" in res.data, err_msg

        res = self.new_team(name="TestTeam")
        assert "Team created" in res.data, res
        self.signout()

    def test_05_team_add_anonymous(self):
        ''' Test 05 TEAM create a team as anonymous user'''
        res = self.app.get("/team/myteams", follow_redirects=True)
        err_msg = ("The anonymous user should not be able to access"
                  "but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in res.data, err_msg

    def test_06_team_add_public(self):
        ''' Test 06 TEAM create a team check'''
        self.register()

        res = self.new_team(name='')
        assert "Team Name must be between 3 and 35 characters long" in \
            res.data, res

        res = self.new_team(description='')
        assert "Team Description must be between 3 and 35 characters long" in \
        res.data, res

        res = self.new_team()
        assert "Team created" in res.data, res

        team = db.session.query(model.Team).get(1)
        assert team.public, "Team must be public"

        res = self.new_team()
        assert "The team name is already taken" in res.data, res

        res = self.new_team(name='Team2')
        assert "Team created" in res.data, res

        assert  db.session.query(model.Team).count() == 2, "Fault in creation teams"
        self.signout()

    def test_07_team_public_view_anonymous(self):
        ''' Test 07 TEAM is an anonymous user can see a public team
        All people can see the public profile of a team
        wiht /team/<name>
        '''
        _teamname = "TeamTest"
        self.register()
        res = self.new_team(name=_teamname)
        self.signout()

        res = self.app.get("/team", follow_redirects=True)
        err_msg = "You can not see the public team %s" % _teamname
        assert "Please sign in to access this page" in res.data, err_msg

        # User can View Teams Public
        #res = self.app.get("/team/%s" % _teamname, follow_redirects=True)
        #err_msg = "You can not see %s" % _teamname
        #assert "%s" % _teamname  in res.data, err_msg

    def test_08_team_public_view_authenticated(self):
        ''' Test 08 TEAM is an authenticated user can see a public team
        in team
        '''
        _teamname = "TeamTest"
        self.register()
        res = self.new_team(name=_teamname)
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")

        res = self.app.get("/team", follow_redirects=True)
        err_msg = "You can not see the public team %s" % _teamname
        assert "%s" % _teamname in res.data, err_msg
        self.signout()

    def test_09_team_add_public_invitation_only(self):
        ''' Test 09 TEAM create a public_invitation_only '''
        self.register()
        self.new_team(name="TestPublicInvitation",public=False)

        team = db.session.query(model.Team).get(1)
        assert team.public == False, "Team doesn't is False"
        self.signout()

    def test_10_team_public_invitation_only_view_anonymous(self):
        ''' Test 10 TEAM is an anonymous user can see a public invitation
        only team
        '''
        _teamname = "TeamTest"
        self.register()
        res = self.new_team(name=_teamname, public=False)
        self.signout()

        res = self.app.get("/team", follow_redirects=True)
        err_msg = "You can not see the public team %s" % _teamname
        assert "Please sign in to access this page" in res.data, err_msg

    def test_11_team_public_invitation_only_view_authenticated(self):
        ''' Test 11 TEAM is an authenticated user can see a public invitation only
        team
        '''
        _teamname = "TeamTest"
        self.register()
        res = self.new_team(name=_teamname, public=False)
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")

        res = self.app.get("/team", follow_redirects=True)
        err_msg = "An authenticated user can see the public invitation only team %s" % _teamname
        assert ("%s" % _teamname) not in res.data, err_msg
        self.signout()

    def test_12_team_public_invitation_only_view_admin(self):
        ''' Test 12 TEAM is an admin  can see a public invitation only team '''
        _teamname = "TeamTest"
        self.register()
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")

        res = self.new_team(name=_teamname, public=False)
        self.signout()

        self.signin()
        res = self.app.get("/team", follow_redirects=True)
        err_msg = "Admin can see the public invitation team in section public"
        assert ("%s" % _teamname) not in res.data, err_msg

        res = self.app.get("/team/private", follow_redirects=True)
        err_msg = "An admin can not see the public invitation only team \
                in private section"
        assert ("%s" % _teamname) in res.data, err_msg
        self.signout()

    def test_13_team_manage(self):
        ''' Test 13 TEAM update and delete '''
        self.register()
        self.new_team()

        res =  self.update_team()
        err_msg ="Can not update a team"
        assert "Team updated!" in res.data, err_msg

        res =  self.delete_team()
        err_msg = "You can delete your own team"
        assert "Team deleted!" in res.data, err_msg

    def test_14_team_manage_as_anonymous(self):
        ''' Test 14 TEAM update and delete as anonymous user'''
        self.register()
        self.new_team()
        self.signout()

        res =  self.update_team()
        err_msg = "Anonymous user can not delete teams"
        assert "Please sign in to access this page" in res.data, err_msg

        res =  self.update_team()
        err_msg = "Anonymous user can not update teams"
        assert "Please sign in to access this page" in res.data, err_msg

    def test_15_team_public_manage_as_authenticated(self):
        ''' Test 15 TEAM update and delete created by other authenticated user'''
        self.register()
        self.signout()

        ''' #1 Authenticated and created a team '''
        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        self.new_team()
        self.signout()

        ''' #2 Authenticated and try to update #1 team '''
        self.register(username="tester3",
                email="tester3@tester.com",
                password="tester")

        res =  self.update_team()
        err_msg ="You can not update other team of other user"
        assert res.status_code == 401, err_msg

        res =  self.delete_team()
        err_msg ="You can not delete other team of other user"
        assert res.status_code == 401, err_msg
        self.signout()

    def test_16_team_public_manage_as_admin(self):
        ''' Test 16 TEAM update and delete  as admin'''
        self.register()
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        self.new_team()
        self.signout()

        self.signin()
        res =  self.update_team()
        err_msg ="Admin can update all team"
        assert "Team updated!" in res.data, err_msg

        res =  self.delete_team()
        err_msg ="Admin can delete all team"
        assert "Team deleted!" in res.data, err_msg
        self.signout()

    def test_17_team_public_invitation_only_manage_as_admin(self):
        ''' Test 17 TEAM public invitation only update and delete as admin'''
        self.register()
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        self.new_team(public=False)
        self.signout()

        self.signin()
        res =  self.update_team()
        err_msg ="Admin can delete public invitation only team"
        assert "Team updated!" in res.data, err_msg

        res =  self.delete_team()
        err_msg ="Admin can update public invitation only team"
        assert "Team deleted!" in res.data, err_msg
        self.signout()

    def test_18_team_public_manage_non_existent(self):
        ''' Test 18 TEAM try to update a non existent team '''
        self.register()

        res =  self.update_team()
        err_msg ="If a team doesn't exists the response will be 404"
        assert res.status_code == 404, err_msg

        res =  self.delete_team()
        err_msg ="If a team doesn't exists the response will be 404"
        assert res.status_code == 404, err_msg
        self.signout()

    def test_19_team_settings_page(self):
        ''' Test 19 Team buttons '''
        _name = "TeamTest"

        self.register()
        self.new_team(name=_name)
        url = "/team/%s/settings" % _name
        res = self.app.get(url, follow_redirects=True)

        dom = BeautifulSoup(res.data)
        divs = ['edit_team', 'delete_team', 'members']
        for div in divs:
            err_msg = "There should be a button for managing %s" % div
            assert dom.find(id=div) is not None, err_msg
        self.signout()

    def test_20_team_settings_as_anonymous(self):
        ''' Test 20 TEAM update and delete as anonymous user'''
        _name = "TeamTest"
        self.register()
        self.new_team()
        self.signout()

        url = "/team/%s/settings" % _name
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Anonymous user can not settings teams"
        assert "Please sign in to access this page" in res.data, err_msg

    def test_21_team_public_settings_page_as_authenticated(self):
        ''' Test 21 Team buttons for authenticated users'''
        _name = "TeamTest"

        self.register()
        self.new_team(name=_name)
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")

        url = "/team/%s/settings" % _name
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        divs = ['user_add', 'members']
        for div in divs:
            err_msg = "There should be a button for managing %s" % div
            assert dom.find(id=div) is not None, err_msg

        divs = ['edit_team', 'delete_team']
        for div in divs:
            err_msg = "There should not be a button for managing %s" % div
            assert dom.find(id=div) is  None, err_msg

        self.signout()

    def test_22_team_public_settings_page_as_admin(self):
        ''' Test 22 Team public buttons for admins'''
        _name = "TeamTest"
        self.register()
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        self.new_team(name=_name)
        self.signout()

        self.signin()
        url = "/team/%s/settings" % _name
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        divs = ['edit_team', 'user_add', 'delete_team', 'members']
        print res.data
        for div in divs:
            err_msg = "There should be a button for managing %s" % div
            assert dom.find(id=div) is not None, err_msg
        self.signout()

    def test_23_team_public_invitation_only_settings_page_as_admin(self):
        ''' Test 23 Team public invitation only buttons for admins'''
        _name = "TeamTest"
        self.register()
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        self.new_team(name=_name, public=False)
        self.signout()

        self.signin()
        url = "/team/%s/settings" % _name
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        divs = ['edit_team', 'user_add', 'delete_team', 'members']
        print res.data
        for div in divs:
            err_msg = "There should be a button for managing %s" % div
            assert dom.find(id=div) is not None, err_msg
        self.signout()

    def test_24_team_public_join_separate_as_anonymous(self):
        ''' Test 24 Team public join separate as anonymous '''
        _name = "TeamTest"
        self.register()
        self.new_team(name=_name)
        self.signout()

        url = '/team/%s/join' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "Anonymous user can not join teams"
        assert "Please sign in to access this page" in res.data, err_msg

        url = '/team/%s/separate' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "Anonymous user can not separate teams"
        assert "Please sign in to access this page" in res.data, err_msg

    def test_25_team_public_join_separate_as_authenticated(self):
        ''' Test 25 Team public join separate as authenticated user  '''
        _name = "TeamTest"
        _name = "TeamTest"
        self.register()
        self.new_team(name=_name)
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")

        url = '/team/%s/join' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert "Association to the team created"  in res.data, err_msg

        url = '/team/%s/separate' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert "Association to the team deleted"  in res.data, err_msg
        self.signout()

    def test_26_team_public_invi_only_join_separate_as_authenticated(self):
        ''' Test 26 Team public invitation only join separate as
        authenticated user
        '''
        _name = "TeamTest"
        self.register()
        self.new_team(name=_name, public=False)
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")

        url = '/team/%s/join' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert_equal(res.status, '404 NOT FOUND', err_msg)

        url = '/team/%s/separate' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert_equal(res.status, '404 NOT FOUND', err_msg)
        self.signout()

    def test_27_team_public_invi_only_join_separate_as_admin(self):
        ''' Test 27 Team public invitation only join separate as admin '''
        _name = "TeamTest"
        self.register()
        self.signout()

        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")
        self.new_team(name=_name, public=False)
        self.signout()

        self.signin()

        url = '/team/%s/join' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert "Association to the team created"  in res.data, err_msg

        url = '/team/%s/separate' % _name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert "Association to the team deleted"  in res.data, err_msg
        self.signout()

    def test_28_team_public_join_separate_manage_outder(self):
        ''' Test 28 Team public manage outer '''
        _name = "TeamTest"
        # Admin
        self.register()
        self.signout()

        # User 1
        self.register(username="tester1",
                email="tester1@tester.com",
                password="tester")
        self.new_team(name=_name)
        self.signout()

        # User 2
        self.register(username="tester2",
                email="tester2@tester.com",
                password="tester")

        # User 3
        self.register(username="tester3",
                email="tester3@tester.com",
                password="tester")

        # User 1 try to add User 2 to its team
        self.signin(email="tester1@tester.com", password="tester")
        url = '/team/%s/join/%s'  % (_name, "tester2")
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert "Association to the team created"  in res.data, err_msg

        url = '/team/%s/separate/%s'  % (_name, "tester2")
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not separate to this team"
        assert "Association to the team deleted"  in res.data, err_msg
        self.signout()

        # User 3 try to add User 2 to Team owner User 1
        self.signin(email="tester3@tester.com", password="tester")
        url = '/team/%s/join/%s'  % (_name, "tester2")
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert "You do not have right to add to this team!!"  in res.data, err_msg
        self.signout()

        # Admin try to add User 2 to Team owner User 1
        self.signin(email="johndoe@example.com", password="p4ssw0rd")
        url = '/team/%s/join/%s'  % (_name, "tester3")
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not join to this team"
        assert "Association to the team created"  in res.data, err_msg

        url = '/team/%s/separate/%s'  % (_name, "tester3")
        res = self.app.post(url, follow_redirects=True)
        err_msg = "You can not separate to this team"
        assert "Association to the team deleted"  in res.data, err_msg

        self.signout()
