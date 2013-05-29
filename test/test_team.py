from helper import web
from base import model, db, Fixtures
from nose.tools import assert_equal

class TestTeams(web.Helper):
   # Helper functions
   def new_team(self, method="POST",
                      name="TeamTest",
                      description="Team TestDescription",
                      public="True",
                      owner=1):

       ''' Test TEAM create team work'''
       if method == "POST":
           if public == True:
             return self.app.post('/team/new/', 
                                 data={'name':        name,
                                       'description': description,
                                       'public':      public,
                                       'owner':       owner
                                      }, 
                                  follow_redirects=True)
           else:
             return self.app.post('/team/new/', 
                                 data={'name':        name,
                                       'description': description,
                                       'owner':       owner
                                      }, 
                                 follow_redirects=True)
       else:
           return self.app.get("/team/new/", follow_redirects=True)

   def delete_team(self, method="POST", name="TeamTest",
            description="Team TestDescription", public=True):
       ''' Test TEAM delete team work'''
       if method == "POST":
           return self.app.post("/team/%s/delete" % name,
                                follow_redirects=True)

       else:
           return self.app.get("/team/%s/delete" % name,
                                follow_redirects=True)


   def update_team(self, method="POST", name="TeamTest",
           new_name="Team Sample",
           new_description="Team Sample Description",
           new_public=True):

       ''' Test TEAM update team work'''
       if method == "POST":
           return self.app.post("/team/%s/update" % name, data={
                                'name': new_name,
                                'description': new_description,
                                'public': new_public
                  }, follow_redirects=True)
       else:
           return self.app.get("/team/%s/update" % name,
                               follow_redirects=True)

   def test_00_team_index(self):
       ''' Test 00 TEAM index page works'''
       res = self.app.get("/team", follow_redirects=True)
 
       err_msg = "There would be a team public page"
       assert  "Public Teams" in res.data, err_msg

   def test_01_team_add(self):
       ''' Test 01 TEAM create a team'''
       self.register()

       res = self.app.get("/team/myteams", follow_redirects=True)
       err_msg = "There should be a button for Create Team"
       print res.data
       assert "Create new Team" in res.data, err_msg
      
       res = self.new_team(name="TestTeam")
       assert "Team created" in res.data, res
      
       self.signout

       team = db.session.query(model.Team).get(1)
       assert team.name == "TestTeam", "Team does not created"

   def test_02_team_add_check(self):
       ''' Test 02 TEAM create a team check'''
       self.register()

       res = self.new_team(name='')
       assert "Team Name must be between 3 and 35 characters long" in res.data, res

       res = self.new_team(description='')
       assert "Team Description must be between 3 and 35 characters long" in res.data, re

       res = self.new_team()
       assert "Team created" in res.data, res

       res = self.new_team()
       assert "The team name is already taken" in res.data, res

       res = self.new_team(name='Team2')
       assert "Team created" in res.data, res

       self.signout()

   def test_03_team_add_private(self):
       ''' Test 03 TEAM create a private team '''
       self.register()
       self.new_team(name="TestPrivate",public=False)
       
       team = db.session.query(model.Team).get(1)
       assert team.public == False, "Team doesn't is False"
       self.signout()

   def test_04_team_views_public(self):
       ''' Test 04 TEAM views '''
       # First Create a public Team
       self.register()
       self.new_team(name="User1Team", public=True)
       self.signout()  

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       # User can View Teams Public
       res = self.app.get("/team", follow_redirects=True)
       err_msg = "You can not see User1 Team"
       assert "User1Team" in res.data, err_msg

       # User can Join
       err_msg = "You can not add to the team"
       assert "Join this team" in res.data, err_msg
       
       # Access by url
       res = self.app.get("/team/User1Team", follow_redirects=True)
       err_msg = "You can not add to the team"
       assert "Join this team" in res.data, err_msg
       
       self.signout()

   def test_05_team_views_private(self):
       ''' Test 05 TEAM views private '''
       # First Create a private Team
       self.register()
       self.new_team(name="User1Team", public=False)
       self.signout()  

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       # View Teams Public
       res = self.app.get("/team", follow_redirects=True)
       err_msg = "You can not see User1 Team"
       assert "User1Team" not in res.data, err_msg

       # Access by url
       res = self.app.get("/team/User1Team", follow_redirects=True)
       err_msg = "You can access to  User1 Team"
       assert "We didn't this team" not in res.data, err_msg

       self.signout()

   def test_06_team_views_admin(self):
       ''' Test 06 TEAM views admin '''
       # First Create Admin User
       self.register()
       self.signout()  

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       # Creat Team Private
       self.new_team(name="User2Team", public=False)
       self.signout()  

       # Register as Admin
       self.register()
       res = self.app.get("/team", follow_redirects=True)
       err_msg = "You can not see Private Team user"
       assert "User2Team" not in res.data, err_msg

       # Access by url
       res = self.app.get("/team/User2Team", follow_redirects=True)
       err_msg = "You can access to User2 Team"
       assert "Join this team " not in res.data, err_msg
       
       # Edit Button
       res = self.app.get("/team/User2Team", follow_redirects=True)
       err_msg = "You can not Edit User2 Team"
       assert "Edit" not in res.data, err_msg
       
       # Delete Button
       res = self.app.get("/team/User2Team", follow_redirects=True)
       err_msg = "You can not Delete User2 Team"
       assert "Delete" not in res.data, err_msg

       # Add User Button
       res = self.app.get("/team/User2Team", follow_redirects=True)
       err_msg = "You can not Add User to User2 Team"
       assert "Add User" not in res.data, err_msg

       self.signout()

   def test_07_team_delete(self):
       ''' Test 07 TEAM delete '''
       self.register()
       self.new_team()
       res =  self.delete_team()
       assert "Team deleted!" in res.data, res
       self.signout()

   def test_08_team_update(self):
       ''' Test 08 TEAM update '''
       self.register()
       self.new_team()

       res =  self.update_team()
       assert "Team updated!" in res.data, res
       self.signout()

   def test_09_team_delete_dont_exists(self):
       ''' Test 09 TEAM delete doesn't exists'''
       self.register()
       res =  self.delete_team(name='Team not exists')
       print res.status
       error_msg = "You don\'t delete a not exists team"
       assert_equal(res.status, '404 NOT FOUND', error_msg)
       self.signout()

   def test_10_join_team_public(self):
       ''' Test 10 TEAM join to a public team '''
       _name = "User1Team"

       self.register()
       self.new_team(name=_name, public=True)
       self.signout()

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       res = self.app.get("/team/%s/join" % _name, follow_redirects=True)
       err_msg = "You can not join to the Team"
       assert "Join this team " not in res.data, err_msg
       
       res = self.app.get("/team/%s/join" % _name, follow_redirects=True)
       err_msg = "You can not associate to the team"
       assert "This user already is in this team"  in res.data, err_msg

       res = self.app.get("/team/%s/separate" % _name, follow_redirects=True)
       err_msg = "You can not left to the Team"
       assert "Left this team " not in res.data, err_msg
       
       self.signout()

   def test_11_join_team_private(self):
       ''' Test 11 TEAM join to a private team '''
       _name = "User1Team"

       self.register()
       self.new_team(name=_name)
       self.signout()

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       res = self.app.get("/team/%s" % _name, follow_redirects=True)

       error_msg = "You don\'t see a private team"
       assert_equal(res.status, '404 NOT FOUND', error_msg)
       self.signout() 

   def test_12_manage_team(self):
       ''' Test 12 TEAM manage '''
       _name = "User1Team"
       _username = "tester1"

       self.register()
       self.new_team(name=_name, public=True)
       self.signout()

       self.register(username= _username, email="tester2@tester.com",
                      password="tester")

       res = self.app.get("/team/%s/join" % _name, follow_redirects=True)
       err_msg = "You can not associate to the team"
       assert "Association to the team created"  in res.data, err_msg
       self.signout()

       self.signin()
       res = self.app.get("/team/%s/users" % _name, follow_redirects=True)
       print res.data
       err_msg = "You can not add user to the Team"
       assert "Add Users" in res.data, err_msg

       err_msg = "You can not remove an user in the  Team"
       assert "Remove" in res.data, err_msg

       res = self.app.get("/team/%s/separate/%s" % (_name, _username) , follow_redirects=True)
       err_msg = "You can not delete a user by url"
       assert "The user has been deleted to the team correctly" in res.data, err_msg

       res = self.app.get("/team/%s/join/%s" % (_name, _username) , follow_redirects=True)
       err_msg = "You can not add user by url"
       assert "Association to the team created" in res.data, err_msg

       self.signout()
