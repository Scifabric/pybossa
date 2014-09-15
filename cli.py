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
                          description='Volunteer Thinking projects'))
        categories.append(Category(name="Volunteer Sensing",
                          short_name='sensing',
                          description='Volunteer Sensing projects'))
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
    """Download current links from user avatar and projects to real images hosted in the
    PyBossa server."""
    import requests
    import os
    import time
    from urlparse import urlparse
    from PIL import Image

    def get_gravatar_url(email, size):
        # import code for encoding urls and generating md5 hashes
        import urllib, hashlib

        # construct the url
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':404, 's':str(size)})
        return gravatar_url

    with app.app_context():
        if app.config['UPLOAD_METHOD'] == 'local':
            users = User.query.order_by('id').all()
            print "Downloading avatars for %s users" % len(users)
            for u in users[0:10]:
                print "Downloading avatar for %s ..." % u.name
                container = "user_%s" % u.id
                path = os.path.join(app.config.get('UPLOAD_FOLDER'), container)
                try:
                    print get_gravatar_url(u.email_addr, 100)
                    r = requests.get(get_gravatar_url(u.email_addr, 100), stream=True)
                    if r.status_code == 200:
                        if not os.path.isdir(path):
                            os.makedirs(path)
                        prefix = time.time()
                        filename = "%s_avatar.png" % prefix
                        with open(os.path.join(path, filename), 'wb') as f:
                            for chunk in r.iter_content(1024):
                                f.write(chunk)
                        u.info['avatar'] = filename
                        u.info['container'] = container
                        db.session.commit()
                        print "Done!"
                    else:
                        print "No Gravatar, this user will use the placeholder."
                except:
                    raise
                    print "No gravatar, this user will use the placehoder."


            apps = App.query.all()
            print "Downloading avatars for %s projects" % len(apps)
            for a in apps[0:1]:
                if a.info.get('thumbnail') and not a.info.get('container'):
                    print "Working on project: %s ..." % a.short_name
                    print "Saving avatar: %s ..." % a.info.get('thumbnail')
                    url = urlparse(a.info.get('thumbnail'))
                    if url.scheme and url.netloc:
                        container = "user_%s" % a.owner_id
                        path = os.path.join(app.config.get('UPLOAD_FOLDER'), container)
                        try:
                            r = requests.get(a.info.get('thumbnail'), stream=True)
                            if r.status_code == 200:
                                prefix = time.time()
                                filename = "app_%s_thumbnail_%i.png" % (a.id, prefix)
                                if not os.path.isdir(path):
                                    os.makedirs(path)
                                with open(os.path.join(path, filename), 'wb') as f:
                                    for chunk in r.iter_content(1024):
                                        f.write(chunk)
                                a.info['thumbnail'] = filename
                                a.info['container'] = container
                                db.session.commit()
                                print "Done!"
                        except:
                            print "Something failed, this project will use the placehoder."
        if app.config['UPLOAD_METHOD'] == 'rackspace':
            import pyrax
            import tempfile
            pyrax.set_setting("identity_type", "rackspace")
            pyrax.set_credentials(username=app.config['RACKSPACE_USERNAME'],
                                  api_key=app.config['RACKSPACE_API_KEY'],
                                  region=app.config['RACKSPACE_REGION'])

            cf = pyrax.cloudfiles
            users = User.query.all()
            print "Downloading avatars for %s users" % len(users)
            dirpath = tempfile.mkdtemp()
            for u in users:
                try:
                    r = requests.get(get_gravatar_url(u.email_addr, 100), stream=True)
                    if r.status_code == 200:
                        print "Downloading avatar for %s ..." % u.name
                        container = "user_%s" % u.id
                        try:
                            cf.get_container(container)
                        except pyrax.exceptions.NoSuchContainer:
                            cf.create_container(container)
                            cf.make_container_public(container)
                        prefix = time.time()
                        filename = "%s_avatar.png" % prefix
                        with open(os.path.join(dirpath, filename), 'wb') as f:
                            for chunk in r.iter_content(1024):
                                f.write(chunk)
                        chksum = pyrax.utils.get_checksum(os.path.join(dirpath,
                                                                       filename))
                        cf.upload_file(container,
                                       os.path.join(dirpath, filename),
                                       obj_name=filename,
                                       etag=chksum)
                        u.info['avatar'] = filename
                        u.info['container'] = container
                        db.session.commit()
                        print "Done!"
                    else:
                        print "No Gravatar, this user will use the placeholder."
                except:
                    print "No gravatar, this user will use the placehoder."


            apps = App.query.all()
            print "Downloading avatars for %s projects" % len(apps)
            for a in apps:
                if a.info.get('thumbnail') and not a.info.get('container'):
                    print "Working on project: %s ..." % a.short_name
                    print "Saving avatar: %s ..." % a.info.get('thumbnail')
                    url = urlparse(a.info.get('thumbnail'))
                    if url.scheme and url.netloc:
                        container = "user_%s" % a.owner_id
                        try:
                            cf.get_container(container)
                        except pyrax.exceptions.NoSuchContainer:
                            cf.create_container(container)
                            cf.make_container_public(container)

                        try:
                            r = requests.get(a.info.get('thumbnail'), stream=True)
                            if r.status_code == 200:
                                prefix = time.time()
                                filename = "app_%s_thumbnail_%i.png" % (a.id, prefix)
                                with open(os.path.join(dirpath, filename), 'wb') as f:
                                    for chunk in r.iter_content(1024):
                                        f.write(chunk)
                                chksum = pyrax.utils.get_checksum(os.path.join(dirpath,
                                                                               filename))
                                cf.upload_file(container,
                                               os.path.join(dirpath, filename),
                                               obj_name=filename,
                                               etag=chksum)
                                a.info['thumbnail'] = filename
                                a.info['container'] = container
                                db.session.commit()
                                print "Done!"
                        except:
                            print "Something failed, this project will use the placehoder."


def resize_avatars():
    """Resize avatars to 512px."""
    if app.config['UPLOAD_METHOD'] == 'rackspace':
        import pyrax
        import tempfile
        import requests
        from PIL import Image
        import time
        pyrax.set_setting("identity_type", "rackspace")
        pyrax.set_credentials(username=app.config['RACKSPACE_USERNAME'],
                              api_key=app.config['RACKSPACE_API_KEY'],
                              region=app.config['RACKSPACE_REGION'])

        cf = pyrax.cloudfiles
        user_id_updated_avatars = []
        if os.path.isfile('user_id_updated_avatars.txt'):
            f = open('user_id_updated_avatars.txt', 'r')
            user_id_updated_avatars = f.readlines()
            f.close()
        users = User.query.filter(~User.id.in_(user_id_updated_avatars)).all()
        print "Downloading avatars for %s users" % len(users)
        dirpath = tempfile.mkdtemp()
        f = open('user_id_updated_avatars.txt', 'a')
        for u in users:
            try:
                cont = cf.get_container(u.info['container'])
                avatar_url = "%s/%s" % (cont.cdn_uri, u.info['avatar'])
                r = requests.get(avatar_url, stream=True)
                if r.status_code == 200:
                    print "Downloading avatar for %s ..." % u.name
                    #container = "user_%s" % u.id
                    #try:
                    #    cf.get_container(container)
                    #except pyrax.exceptions.NoSuchContainer:
                    #    cf.create_container(container)
                    #    cf.make_container_public(container)
                    prefix = time.time()
                    filename = "%s_avatar.png" % prefix
                    with open(os.path.join(dirpath, filename), 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                    # Resize image
                    im = Image.open(os.path.join(dirpath, filename))
                    size = 512, 512
                    tmp = im.resize(size, Image.ANTIALIAS)
                    scale_down_img = tmp.convert('P', colors=255, palette=Image.ADAPTIVE)
                    scale_down_img.save(os.path.join(dirpath, filename), format='png')

                    print "New scaled down image created!"
                    print "%s" % (os.path.join(dirpath, filename))
                    print "---"

                    chksum = pyrax.utils.get_checksum(os.path.join(dirpath,
                                                                   filename))
                    cf.upload_file(cont,
                                   os.path.join(dirpath, filename),
                                   obj_name=filename,
                                   etag=chksum)
                    old_avatar = u.info['avatar']
                    # Update new values
                    u.info['avatar'] = filename
                    u.info['container'] = "user_%s" % u.id
                    db.session.commit()
                    # Save the user.id to avoid downloading it again.
                    f.write("%s\n" % u.id)
                    # delete old avatar
                    obj = cont.get_object(old_avatar)
                    obj.delete()
                    print "Done!"
                else:
                    print "No Avatar found."
            except pyrax.exceptions.NoSuchObject:
                print "Previous avatar not found, so not deleting it."
            except:
                raise
                print "No Avatar, this user will use the placehoder."
        f.close()

def resize_project_avatars():
    """Resize project avatars to 512px."""
    if app.config['UPLOAD_METHOD'] == 'rackspace':
        import pyrax
        import tempfile
        import requests
        from PIL import Image
        import time
        import pybossa.cache.apps as cached_apps
        # Disable cache to update the data in it :-)
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'
        pyrax.set_setting("identity_type", "rackspace")
        pyrax.set_credentials(username=app.config['RACKSPACE_USERNAME'],
                              api_key=app.config['RACKSPACE_API_KEY'],
                              region=app.config['RACKSPACE_REGION'])

        cf = pyrax.cloudfiles

        #apps = App.query.all()
        file_name = 'project_id_updated_thumbnails.txt'
        project_id_updated_thumbnails = []
        if os.path.isfile(file_name):
            f = open(file_name, 'r')
            project_id_updated_thumbnails = f.readlines()
            f.close()
        apps = App.query.filter(~App.id.in_(project_id_updated_thumbnails)).all()
        #apps = [App.query.get(2042)]
        print "Downloading avatars for %s projects" % len(apps)
        dirpath = tempfile.mkdtemp()
        f = open(file_name, 'a')
        for a in apps:
            try:
                cont = cf.get_container(a.info['container'])
                avatar_url = "%s/%s" % (cont.cdn_uri, a.info['thumbnail'])
                r = requests.get(avatar_url, stream=True)
                if r.status_code == 200:
                    print "Downloading avatar for %s ..." % a.short_name
                    prefix = time.time()
                    filename = "app_%s_thumbnail_%s.png" % (a.id, prefix)
                    with open(os.path.join(dirpath, filename), 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                    # Resize image
                    im = Image.open(os.path.join(dirpath, filename))
                    size = 512, 512
                    tmp = im.resize(size, Image.ANTIALIAS)
                    scale_down_img = tmp.convert('P', colors=255, palette=Image.ADAPTIVE)
                    scale_down_img.save(os.path.join(dirpath, filename), format='png')

                    print "New scaled down image created!"
                    print "%s" % (os.path.join(dirpath, filename))
                    print "---"

                    chksum = pyrax.utils.get_checksum(os.path.join(dirpath,
                                                                   filename))
                    cf.upload_file(cont,
                                   os.path.join(dirpath, filename),
                                   obj_name=filename,
                                   etag=chksum)
                    old_avatar = a.info['thumbnail']
                    # Update new values
                    a.info['thumbnail'] = filename
                    #a.info['container'] = "user_%s" % u.id
                    db.session.commit()
                    f.write("%s\n" % a.id)
                    # delete old avatar
                    obj = cont.get_object(old_avatar)
                    obj.delete()
                    print "Done!"
                    cached_apps.get_app(a.short_name)
                else:
                    print "No Avatar found."
            except pyrax.exceptions.NoSuchObject:
                print "Previous avatar not found, so not deleting it."
            except:
                raise
                print "No Avatar, this project will use the placehoder."
        f.close()
        #    if a.info.get('thumbnail') and not a.info.get('container'):
        #        print "Working on project: %s ..." % a.short_name
        #        print "Saving avatar: %s ..." % a.info.get('thumbnail')
        #        url = urlparse(a.info.get('thumbnail'))
        #        if url.scheme and url.netloc:
        #            container = "user_%s" % a.owner_id
        #            try:
        #                cf.get_container(container)
        #            except pyrax.exceptions.NoSuchContainer:
        #                cf.create_container(container)
        #                cf.make_container_public(container)

        #            try:
        #                r = requests.get(a.info.get('thumbnail'), stream=True)
        #                if r.status_code == 200:
        #                    prefix = time.time()
        #                    filename = "app_%s_thumbnail_%i.png" % (a.id, prefix)
        #                    with open(os.path.join(dirpath, filename), 'wb') as f:
        #                        for chunk in r.iter_content(1024):
        #                            f.write(chunk)
        #                    chksum = pyrax.utils.get_checksum(os.path.join(dirpath,
        #                                                                   filename))
        #                    cf.upload_file(container,
        #                                   os.path.join(dirpath, filename),
        #                                   obj_name=filename,
        #                                   etag=chksum)
        #                    a.info['thumbnail'] = filename
        #                    a.info['container'] = container
        #                    db.session.commit()
        #                    print "Done!"
        #            except:
        #                print "Something failed, this project will use the placehoder."




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


