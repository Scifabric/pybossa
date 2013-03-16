Instructions to heroku deploy
============================

- git clone pybossa, etc get this repo
- gem install heroku if you already dont have it
- follow pybossa instructions to run locally or look for foreman to automate it

These instructions are specific to heroku:

$ heroku create pybossa_instance_name -s cedar
$ git remote add heroku git@heroku.com:pybossa_instance_name.git
$ heroku addons:add heroku-postgresql

Adding a PostgreSQL addon will generate some output, in which Heroku will
emit a string like as HEROKU_POSTGRESQL_(colour)_URL. You can run

$ heroku config

To see what colour-code your database received. You must run

$ heroku pg:promote HEROKU_POSTGRESQL_(colour)_URL

To make this the primary database for your app. The Heroku integration
in PyBossa depends on your having done this.

$ git push heroku master

$ heroku run "python cli.py db_create"
$ heroku ps:scale web=1
$ heroku open (should take some time on the first run)
$ heroku logs 

