### Instructions to heroku deploy

- git clone pybossa, etc get this repo
- gem install heroku if you already dont have it
- follow pybossa instructions to run locally or look for foreman to automate it

These instructions are specific to heroku:

$ heroku create pybossa_instance_name -s cedar
$ heroku addons:add shared-database
$ git submodule init
$ git submodule update

Configure alembic.ini

$ cp alembic.ini.template alembic.ini
$ heroku config | grep SHARED_DATABASE_URL

use the SHARED_DATABASE_URL value for sqlalchemy.url

$ vi alembic.ini

settings_local.py should get this from os.environment but double check it in case of error

$ git add settings_local.py alembic.ini -f
$ git commit -m 'initial setup'
$ git push heroku master

$ heroku run "python cli.py db_create"
$ heroku ps:scale web=1
$ heroku open (should take some time on the first run)
$ heroku logs 

test, etc

Heroku adds another upstream repo to your local repo. To any change there, always remember to git push heroku master (or your branch)

Enjoy


gleicon (http://github.com/gleicon)


