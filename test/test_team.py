from helper import web
from base import model, db, Fixtures

class TestTeams(web.Helper):
   # Helper functions
   def html_title(self, title=None):
       """Helper function to create an HTML title"""
       if title == None:
           return "<title>PyBossa</title>"
       else:
           return "<title>PyBossa &middot; %s</title>" % title

   def test_00_team_index(self):
       ''' Test 00 TEAM index page works'''
       self.register()
       res = self.app.get("/team", follow_redirects=True)
       err_msg = "There should be an index page for create team"
       assert "Team" in res.data, err_msg

       err_msg = "There should be a button for Create your own Team"
       assert "Create your own Team" in res.data, err_msg

       err_msg = "There should be a button for Join to an existing team"
       assert "Join to an existing team" in res.data, err_msg

   def new_team(self, method="POST", 
                      name="TeamTest",
                      description="Team TestDescription", 
                      public="True",
                      owner=1):
       ''' Test TEAM create team work'''
       if method == "POST":
           if public == True: 
             return self.app.post("/team/register", data={
               'name':        name,
               'description': description,
               'public':      public,
               'owner':       owner
                }, follow_redirects=True)
           else:
             return self.app.post("/team/register", data={
               'name':        name,
               'description': description,
               'owner':       owner
                }, follow_redirects=True)
       else:
           return self.app.get("/team/register", follow_redirects=True)

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


   def add_join(self, method="POST", team_id=1):
       ''' Test TEAM create join'''
       if method == "POST":
           return self.app.post("/team/join", data={
                               'team':team_id,
                                },follow_redirects=True)
       else:
           return self.app.get("/team/join", follow_redirects=True)

   def test_01_team_create(self):
       ''' Test 01 TEAM create '''
       self.register()

       res = self.new_team(method="GET")
       assert res.mimetype == 'text/html', res

       res = self.new_team()
       assert "Team successfully created" in res.data, res

       res = self.new_team()
       assert "The team name is already taken" in res.data, res

       res = self.new_team(name='')
       assert "Team Name must be between 3 and 50 characters long" in res.data, res

       res = self.new_team(description='')
       assert "Team Description must be between 3 and 200 characters long" in res.data, res

   def test_02_team_create_private(self):
       ''' Test 02 TEAM create not public '''
       self.register()

       self.new_team(name="TestPublic",public=False)
       team = db.session.query(model.Team).get(1)
       assert team.public == False, "Team doesn't is False"
  
   def test_03_team_delete(self):
       ''' Test 03 TEAM delete '''
       self.register()
       self.new_team()

       res =  self.delete_team()
       assert "Your team has been deleted!" in res.data, res

   def test_04_team_delete(self):
       ''' Test 04 TEAM delete doesn't exists'''
       self.register()
       res =  self.delete_team(name='Team not exists')
       assert "Oopps, The group that you try to delete doesn\t exists or you don\t are the owner." in res.data, res

   def test_05_team_update(self):
       ''' Test 05 TEAM update '''
       self.register()
       self.new_team()

       res =  self.update_team()
       assert "Your team has been updated!" in res.data, res

   def test_06_team_update(self):
       ''' Test 06 TEAM update doesn't exists'''
       self.register()

       res =  self.update_team(name='Team not exists')
       assert "Oopps, The group that you try to update doesn\t exists or you don\t are the owner." in res.data, res

   def test_07_join_page(self):
       ''' Test 07 TEAM join page owner team '''
       self.register()

       res = self.app.get("/team/join", follow_redirects=True)
       err_msg = "There should be a page for Join Team"
       assert "Add Team" in res.data, err_msg
 
   def test_08_add_join_own_team(self):
       ''' Test 08 TEAM join add own team '''
       self.register()
       self.new_team()

       res = self.add_join()
       assert "Association with the team successfully created!" in res.data, res

   def test_09_delete_join_own_team(self):
       ''' Test 09 TEAM delete join own team '''
       self.register()
       self.new_team()

       res = self.add_join()
       assert "Association with the team successfully created!" in res.data, res

       res = self.app.get('/team/join/1/delete', follow_redirects=True)
       assert "Association with the team deleted" in res.data, res

   def test_10_join_add_outside_team_public(self):
       ''' Test 10 TEAM join add outer public team '''
       self.register()
       self.new_team(name="Team_01", public=True)
       self.signout()

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       res= self.add_join()
       assert "Association with the team successfully created!" in res.data, res
  
   def test_11_join_outside_team_private(self):
       ''' Test 11 TEAM join add outer private team '''
       self.register()
       self.new_team(name="Team_01", public=False)
       self.signout()

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       res= self.add_join()
       assert "Association created, pending approval by the owner" in res.data, res

   def test_12_delete_outside_team_private(self):
       ''' Test 12 TEAM delete join outer private team '''
       self.register()
       self.new_team(name="Team_01", public=False)
       self.signout()

       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")

       self.add_join()
       page = '/team/join/1/delete'
              
       res = self.app.get(page, follow_redirects=True)
       assert "Association with the team deleted" in res.data, res
 
   def test_13_team_owner_accept_user(self):
       ''' Test 13 TEAM owner accept user in private team '''
       # Register User 1 and create its own team
       self.register()
       self.new_team()
       team = db.session.query(model.Team).get(1)
       self.signout()

       # Register User 2 and join to the public team
       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")
       res = self.add_join()
       self.signout()
       user = db.session.query(model.User).get(2)

       # Signin User 1 and accept user
       self.signin()
       page = '/team/%s/users/%s/update' % (team.name, user.id)
       res = self.app.get(page, follow_redirects=True)
       assert "The user has been joined to the team correctly!" in res.data, res

   def test_14_team_owner_accept_user(self):
       ''' Test 14 TEAM owner refuse user in team '''
       # Register User 1 and create its own team
       self.register()
       self.new_team()
       team = db.session.query(model.Team).get(1)
       self.signout()

       # Register User 2 and join to the public team
       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")
       res = self.add_join()
       self.signout()
       user = db.session.query(model.User).get(2)

       # Signin User 1 and accept user
       self.signin()
       page = '/team/%s/users/%s/delete' % (team.name, user.id)
       res = self.app.get(page, follow_redirects=True)
       assert "The user has been deleted from the team" in res.data, res


 
   def test_15_team_owner_accept_user(self):
       ''' Test 15 TEAM owner accept user in private team '''
       # Register User 1 and create its own team
       self.register()
       self.new_team()
       team = db.session.query(model.Team).get(1)
       self.signout()

       # Register User 2 and join to the public team
       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")
       res = self.add_join()
       self.signout()
       user = db.session.query(model.User).get(2)

       # Signin User 1 and accept user
       self.signin()
       page = '/team/%s/users/%s/update' % (team.name, user.id)
       res = self.app.get(page, follow_redirects=True)
       assert "The user has been joined to the team correctly" in res.data, res

   def test_16_team_owner_accept_user(self):
       ''' Test 16 TEAM owner refuse user in team '''
       # Register User 1 and create its own team
       self.register()
       self.new_team()
       team = db.session.query(model.Team).get(1)
       self.signout()

       # Register User 2 and join to the public team
       self.register(username="tester2", email="tester2@tester.com",
                      password="tester")
       res = self.add_join()
       self.signout()
       user = db.session.query(model.User).get(2)

       # Signin User 1 and accept user
       self.signin()
       page = '/team/%s/users/%s/delete' % (team.name, user.id)
       res = self.app.get(page, follow_redirects=True)
       assert "The user has been deleted from the team" in res.data, res

