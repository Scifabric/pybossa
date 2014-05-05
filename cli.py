#!/usr/bin/env python
import os
import sys
import optparse
import inspect

#import pybossa.model as model
from pybossa.core import db, create_app
from pybossa.model.app import App
from pybossa.model.user import User
from pybossa.model.category import Category

from alembic.config import Config
from alembic import command
from html2text import html2text
from sqlalchemy.sql import text

app = create_app()

def setup_alembic_config():
    if "DATABASE_URL" not in os.environ:
        alembic_cfg = Config("alembic.ini")
    else:
        dynamic_filename = "alembic-heroku.ini"
        with file("alembic.ini.template") as f:
            with file(dynamic_filename, "w") as conf:
                for line in f.readlines():
                    if line.startswith("sqlalchemy.url"):
                        conf.write("sqlalchemy.url = %s\n" %
                                   os.environ['DATABASE_URL'])
                    else:
                        conf.write(line)
        alembic_cfg = Config(dynamic_filename)

    command.stamp(alembic_cfg, "head")

def db_create():
    '''Create the db'''
    with app.app_context():
        db.create_all()
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:
        setup_alembic_config()
        # finally, add a minimum set of categories: Volunteer Thinking, Volunteer Sensing, Published and Draft
        categories = []
        categories.append(Category(name="Thinking",
                          short_name='thinking',
                          description='Volunteer Thinking apps'))
        categories.append(Category(name="Volunteer Sensing",
                          short_name='sensing',
                          description='Volunteer Sensing apps'))
        db.session.add_all(categories)
        db.session.commit()

def db_rebuild():
    '''Rebuild the db'''
    with app.app_context():
        db.drop_all()
        db.create_all()
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:
        setup_alembic_config()

def fixtures():
    '''Create some fixtures!'''
    with app.app_context():
        user = User(
            name=u'tester',
            email_addr=u'tester@tester.org',
            api_key='tester'
            )
        user.set_password(u'tester')
        db.session.add(user)
        db.session.commit()

def markdown_db_migrate():
    '''Perform a migration of the app long descriptions from HTML to
    Markdown for existing database records'''
    with app.app_context():
        query = 'SELECT id, long_description FROM "app";'
        query_result = db.engine.execute(query)
        old_descriptions = query_result.fetchall()
        for old_desc in old_descriptions:
            if old_desc.long_description:
                new_description = html2text(old_desc.long_description)
                query = text('''
                           UPDATE app SET long_description=:long_description
                           WHERE id=:id''')
                db.engine.execute(query, long_description = new_description, id = old_desc.id)


def bootstrap_avatars():
    """Download current links from user avatar and apps to real images hosted in the
    PyBossa server."""
    import requests
    import os
    import time
    from urlparse import urlparse
    with app.app_context():
        if app.config['UPLOAD_METHOD'] == 'local':
            apps = App.query.all()
            print "Downloading avatars for %s apps" % len(apps)
            for a in apps:
                if a.info.get('thumbnail') and not a.info.get('container'):
                    print "Working on app: %s ..." % a.short_name
                    print "Saving avatar: %s ..." % a.info.get('thumbnail')
                    url = urlparse(a.info.get('thumbnail'))
                    if url.scheme and url.netloc:
                        container = "user_%s" % a.owner_id
                        path = os.path.join(app.config.get('UPLOAD_FOLDER'), container)
                        if not os.path.isdir(path):
                            os.makedirs(path)
                        try:
                            r = requests.get(a.info.get('thumbnail'), stream=True)
                            if r.status_code == 200:
                                prefix = time.time()
                                filename = "app_%s_thumbnail_%i.png" % (a.id, prefix)
                                with open(os.path.join(path, filename), 'wb') as f:
                                    for chunk in r.iter_content(1024):
                                        f.write(chunk)
                                a.info['thumbnail'] = filename
                                a.info['container'] = container
                                db.session.commit()
                                print "Done!"
                        except:
                            print "Something failed, this app will use the placehoder."
        else:
            pass


## ==================================================
## Misc stuff for setting up a command line interface

def _module_functions(functions):
    local_functions = dict(functions)
    for k,v in local_functions.items():
        if not inspect.isfunction(v) or k.startswith('_'):
            del local_functions[k]
    return local_functions

def _main(functions_or_object):
    isobject = inspect.isclass(functions_or_object)
    if isobject:
        _methods = _object_methods(functions_or_object)
    else:
        _methods = _module_functions(functions_or_object)

    usage = '''%prog {action}

Actions:
    '''
    usage += '\n    '.join(
        [ '%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name,m)
        in sorted(_methods.items()) ])
    parser = optparse.OptionParser(usage)
    # Optional: for a config file
    # parser.add_option('-c', '--config', dest='config',
    #         help='Config file to use.')
    options, args = parser.parse_args()

    if not args or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    if isobject:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])

__all__ = [ '_main' ]

if __name__ == '__main__':
    _main(locals())


