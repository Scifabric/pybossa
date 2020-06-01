#!/usr/bin/env python
import os
import sys
import optparse
import inspect

#import pybossa.model as model
from pybossa.core import db, create_app
from pybossa.model.project import Project
from pybossa.model.user import User
from pybossa.model.category import Category
from pybossa.util import get_avatar_url

from alembic.config import Config
from alembic import command
from html2text import html2text
from sqlalchemy.sql import text

app = create_app(run_as_server=False)


def setup_alembic_config():
    alembic_cfg = Config("alembic.ini")
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
            name='tester',
            email_addr='tester@tester.org',
            api_key='tester'
        )
        user.set_password('tester')
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
                db.engine.execute(
                    query, long_description=new_description, id=old_desc.id)


def get_thumbnail_urls():
    """Update db records with full urls for avatar and thumbnail
    :returns: Nothing

    """
    with app.app_context():
        if app.config.get('SERVER_NAME'):
            projects = db.session.query(Project).all()
            for project in projects:
                upload_method = app.config.get('UPLOAD_METHOD')
                thumbnail = project.info.get('thumbnail')
                container = project.info.get('container')
                if (thumbnail and container):
                    print("Updating project: %s" % project.short_name)
                    thumbnail_url = get_avatar_url(upload_method, thumbnail,
                                                   container,
                                                   app.config.get('AVATAR_ABSOLUTE',
                                                                  True))
                    project.info['thumbnail_url'] = thumbnail_url
                    db.session.merge(project)
                    db.session.commit()
        else:
            print("Add SERVER_NAME to your config file.")


def get_avatars_url():
    """Update db records with full urls for avatar and thumbnail
    :returns: Nothing

    """
    with app.app_context():
        if app.config.get('SERVER_NAME'):
            users = db.session.query(User).all()
            for user in users:
                upload_method = app.config.get('UPLOAD_METHOD')
                avatar = user.info.get('avatar')
                container = user.info.get('container')
                if (avatar and container):
                    print("Updating user: %s" % user.name)
                    avatar_url = get_avatar_url(upload_method, avatar,
                                                container,
                                                app.config.get('AVATAR_ABSOLUTE'))
                    user.info['avatar_url'] = avatar_url
                    db.session.merge(user)
                    db.session.commit()
        else:
            print("Add SERVER_NAME to your config file.")


def fix_task_date():
    """Fix Date format in Task."""
    import re
    from datetime import datetime
    with app.app_context():
        query = text(
            '''SELECT id, created FROM task WHERE created LIKE ('%Date%')''')
        results = db.engine.execute(query)
        tasks = results.fetchall()
        for task in tasks:
            # It's in miliseconds
            timestamp = int(re.findall(r'\d+', task.created)[0])
            print(timestamp)
            # Postgresql expects this format 2015-05-21T13:19:06.471074
            fixed_created = datetime.fromtimestamp(timestamp/1000)\
                                    .replace(microsecond=timestamp % 1000*1000)\
                                    .strftime('%Y-%m-%dT%H:%M:%S.%f')
            query = text('''UPDATE task SET created=:created WHERE id=:id''')
            db.engine.execute(query, created=fixed_created, id=task.id)


def fix_task_run_created_date():
    """Fix Date format in Task."""
    import re
    from datetime import datetime
    with app.app_context():
        query = text(
            '''SELECT id, created FROM task_run WHERE created LIKE ('\\x%')''')
        results = db.engine.execute(query)
        task_runs = results.fetchall()
        for task_run in task_runs:
            # It's a hex string
            try:
                hex_check = task_run.created.replace('\\x', '')
                int(hex_check, 16)
                fixed_created = bytes.fromhex(hex_check).decode()
            except ValueError:
                fixed_created = task_run.created
            print(fixed_created)
            query = text('''UPDATE task_run SET created=:created WHERE id=:id''')
            db.engine.execute(query, created=fixed_created, id=task_run.id)


def delete_hard_bounces():
    '''Delete fake accounts from hard bounces.'''
    del_users = 0
    fake_emails = 0
    with app.app_context():
        with open('email.csv', 'r') as f:
            emails = f.readlines()
            print("Number of users: %s" % len(emails))
            for email in emails:
                usr = db.session.query(User).filter_by(
                    email_addr=email.rstrip()).first()
                if usr and len(usr.projects) == 0 and len(usr.task_runs) == 0:
                    print("Deleting user: %s" % usr.email_addr)
                    del_users += 1
                    db.session.delete(usr)
                    db.session.commit()
                else:
                    if usr:
                        if len(usr.projects) > 0:
                            print("Invalid email (user owns app): %s" % usr.email_addr)
                        if len(usr.task_runs) > 0:
                            print("Invalid email (user has contributed): %s" % usr.email_addr)
                        fake_emails += 1
                        usr.valid_email = False
                        db.session.commit()
        print("%s users were deleted" % del_users)
        print("%s users have fake emails" % fake_emails)


def bootstrap_avatars():
    """Download current links from user avatar and projects to real images hosted in the
    PYBOSSA server."""
    import requests
    import os
    import time
    from urllib.parse import urlparse
    from PIL import Image

    def get_gravatar_url(email, size):
        # import code for encoding urls and generating md5 hashes
        import urllib.request, urllib.parse, urllib.error
        import hashlib

        # construct the url
        gravatar_url = "http://www.gravatar.com/avatar/" + \
            hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.parse.urlencode({'d': 404, 's': str(size)})
        return gravatar_url

    with app.app_context():
        if app.config['UPLOAD_METHOD'] == 'local':
            users = User.query.order_by('id').all()
            print("Downloading avatars for %s users" % len(users))
            for u in users:
                print("Downloading avatar for %s ..." % u.name)
                container = "user_%s" % u.id
                path = os.path.join(app.config.get('UPLOAD_FOLDER'), container)
                try:
                    print(get_gravatar_url(u.email_addr, 100))
                    r = requests.get(get_gravatar_url(
                        u.email_addr, 100), stream=True)
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
                        print("Done!")
                    else:
                        print("No Gravatar, this user will use the placeholder.")
                except:
                    raise
                    print("No gravatar, this user will use the placehoder.")

            apps = Project.query.all()
            print("Downloading avatars for %s projects" % len(apps))
            for a in apps:
                if a.info.get('thumbnail') and not a.info.get('container'):
                    print("Working on project: %s ..." % a.short_name)
                    print("Saving avatar: %s ..." % a.info.get('thumbnail'))
                    url = urlparse(a.info.get('thumbnail'))
                    if url.scheme and url.netloc:
                        container = "user_%s" % a.owner_id
                        path = os.path.join(app.config.get(
                            'UPLOAD_FOLDER'), container)
                        try:
                            r = requests.get(a.info.get(
                                'thumbnail'), stream=True)
                            if r.status_code == 200:
                                prefix = time.time()
                                filename = "app_%s_thumbnail_%i.png" % (
                                    a.id, prefix)
                                if not os.path.isdir(path):
                                    os.makedirs(path)
                                with open(os.path.join(path, filename), 'wb') as f:
                                    for chunk in r.iter_content(1024):
                                        f.write(chunk)
                                a.info['thumbnail'] = filename
                                a.info['container'] = container
                                db.session.commit()
                                print("Done!")
                        except:
                            print("Something failed, this project will use the placehoder.")
        if app.config['UPLOAD_METHOD'] == 'rackspace':
            import pyrax
            import tempfile
            pyrax.set_setting("identity_type", "rackspace")
            pyrax.set_credentials(username=app.config['RACKSPACE_USERNAME'],
                                  api_key=app.config['RACKSPACE_API_KEY'],
                                  region=app.config['RACKSPACE_REGION'])

            cf = pyrax.cloudfiles
            users = User.query.all()
            print("Downloading avatars for %s users" % len(users))
            dirpath = tempfile.mkdtemp()
            for u in users:
                try:
                    r = requests.get(get_gravatar_url(
                        u.email_addr, 100), stream=True)
                    if r.status_code == 200:
                        print("Downloading avatar for %s ..." % u.name)
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
                        print("Done!")
                    else:
                        print("No Gravatar, this user will use the placeholder.")
                except:
                    print("No gravatar, this user will use the placehoder.")

            apps = Project.query.all()
            print("Downloading avatars for %s projects" % len(apps))
            for a in apps:
                if a.info.get('thumbnail') and not a.info.get('container'):
                    print("Working on project: %s ..." % a.short_name)
                    print("Saving avatar: %s ..." % a.info.get('thumbnail'))
                    url = urlparse(a.info.get('thumbnail'))
                    if url.scheme and url.netloc:
                        container = "user_%s" % a.owner_id
                        try:
                            cf.get_container(container)
                        except pyrax.exceptions.NoSuchContainer:
                            cf.create_container(container)
                            cf.make_container_public(container)

                        try:
                            r = requests.get(a.info.get(
                                'thumbnail'), stream=True)
                            if r.status_code == 200:
                                prefix = time.time()
                                filename = "app_%s_thumbnail_%i.png" % (
                                    a.id, prefix)
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
                                print("Done!")
                        except:
                            print("Something failed, this project will use the placehoder.")


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
            t = open('user_id_updated_avatars.txt', 'r')
            user_id_updated_avatars = t.readlines()
            t.close()
        users = User.query.filter(~User.id.in_(user_id_updated_avatars)).all()
        print("Downloading avatars for %s users" % len(users))
        dirpath = tempfile.mkdtemp()
        f = open('user_id_updated_avatars.txt', 'a')
        for u in users:
            try:
                if u.info.get('container'):
                    cont = cf.get_container(u.info['container'])
                    if cont.cdn_ssl_uri:
                        avatar_url = "%s/%s" % (cont.cdn_ssl_uri,
                                                u.info['avatar'])
                    else:
                        cont.make_public()
                        avatar_url = "%s/%s" % (cont.cdn_ssl_uri,
                                                u.info['avatar'])
                    r = requests.get(avatar_url, stream=True)
                    if r.status_code == 200:
                        print("Downloading avatar for %s ..." % u.name)
                        #container = "user_%s" % u.id
                        # try:
                        #    cf.get_container(container)
                        # except pyrax.exceptions.NoSuchContainer:
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
                        scale_down_img = tmp.convert(
                            'P', colors=255, palette=Image.ADAPTIVE)
                        scale_down_img.save(os.path.join(
                            dirpath, filename), format='png')

                        print("New scaled down image created!")
                        print("%s" % (os.path.join(dirpath, filename)))
                        print("---")

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
                        f = open('user_id_updated_avatars.txt', 'a')
                        f.write("%s\n" % u.id)
                        # delete old avatar
                        obj = cont.get_object(old_avatar)
                        obj.delete()
                        print("Done!")
                    else:
                        print("No Avatar found.")
                else:
                    f.write("%s\n" % u.id)
                    print("No avatar found")
            except pyrax.exceptions.NoSuchObject:
                print("Previous avatar not found, so not deleting it.")
            except:
                raise
                print("No Avatar, this user will use the placehoder.")
        f.close()


def resize_project_avatars():
    """Resize project avatars to 512px."""
    if app.config['UPLOAD_METHOD'] == 'rackspace':
        import pyrax
        import tempfile
        import requests
        from PIL import Image
        import time
        import pybossa.cache.projects as cached_apps
        # Disable cache to update the data in it :-)
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'
        pyrax.set_setting("identity_type", "rackspace")
        pyrax.set_credentials(username=app.config['RACKSPACE_USERNAME'],
                              api_key=app.config['RACKSPACE_API_KEY'],
                              region=app.config['RACKSPACE_REGION'])

        cf = pyrax.cloudfiles

        #apps = Project.query.all()
        file_name = 'project_id_updated_thumbnails.txt'
        project_id_updated_thumbnails = []
        if os.path.isfile(file_name):
            f = open(file_name, 'r')
            project_id_updated_thumbnails = f.readlines()
            f.close()
        apps = Project.query.filter(~Project.id.in_(
            project_id_updated_thumbnails)).all()
        #apps = [Project.query.get(2042)]
        print("Downloading avatars for %s projects" % len(apps))
        dirpath = tempfile.mkdtemp()
        f = open(file_name, 'a')
        for a in apps:
            try:
                if a.info.get('container'):
                    cont = cf.get_container(a.info['container'])
                    avatar_url = "%s/%s" % (cont.cdn_ssl_uri,
                                            a.info['thumbnail'])
                    r = requests.get(avatar_url, stream=True)
                    if r.status_code == 200:
                        print("Downloading avatar for %s ..." % a.short_name)
                        prefix = time.time()
                        filename = "app_%s_thumbnail_%s.png" % (a.id, prefix)
                        with open(os.path.join(dirpath, filename), 'wb') as f:
                            for chunk in r.iter_content(1024):
                                f.write(chunk)
                        # Resize image
                        im = Image.open(os.path.join(dirpath, filename))
                        size = 512, 512
                        tmp = im.resize(size, Image.ANTIALIAS)
                        scale_down_img = tmp.convert(
                            'P', colors=255, palette=Image.ADAPTIVE)
                        scale_down_img.save(os.path.join(
                            dirpath, filename), format='png')

                        print("New scaled down image created!")
                        print("%s" % (os.path.join(dirpath, filename)))
                        print("---")

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
                        f = open(file_name, 'a')
                        f.write("%s\n" % a.id)
                        # delete old avatar
                        obj = cont.get_object(old_avatar)
                        obj.delete()
                        print("Done!")
                        cached_apps.get_app(a.short_name)
                    else:
                        print("No Avatar found.")
                else:
                    print("No avatar found.")
            except pyrax.exceptions.NoSuchObject:
                print("Previous avatar not found, so not deleting it.")
            except:
                raise
                print("No Avatar, this project will use the placehoder.")
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


def password_protect_hidden_projects():
    import random
    from pybossa.core import project_repo, user_repo, mail
    from pybossa.jobs import enqueue_job, send_mail

    def generate_random_password():
        CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        password = ''
        for i in range(8):
            password += random.choice(CHARS)
        return password

    def generate_email_for(project_name, owner_name, password):
        subject = "Changes in your hidden project %s" % project_name
        content = (
            """
Dear %s,

We are writing you to let you know that, due to recent changes in Crowdcrafting,
hidden projects will soon no longer be supported. However, you can still
protect your project with a password, allowing only people with it to
access and contribute to it.

We have checked that your project %s is hidden. We don't want to expose it
to the public, so we have protected it with a password instead. The current
password for your project is:

%s

You will be able to change it on your project settings page.

You can find more information about passwords in the documentation
(http://docs.pybossa.com/user/tutorial/#protecting-the-project-with-a-password).

If you have any doubts, please contact us and we will be pleased to help you!

Best regards,

Crowdcrafting team.
""" % (owner_name, project_name, password))

        return subject, content

    with app.app_context():
        for project in project_repo.filter_by(hidden=1):
            password = generate_random_password()
            subject, content = generate_email_for(
                project.name, project.owner.name, password)
            message = dict(recipients=[project.owner.email_addr],
                           subject=subject,
                           body=content)
            job = dict(name=send_mail,
                       args=[message],
                       kwargs={},
                       timeout=(600),
                       queue='medium')
            enqueue_job(job)
            project.set_password(password)
            project_repo.save(project)


def create_webhooks(projectId):
    """Create webhooks for a given project ID."""
    from pybossa.core import project_repo, task_repo, result_repo
    from pybossa.model.webhook import Webhook

    project = project_repo.get(projectId)
    tasks = task_repo.filter_tasks_by(state='completed',
                                      project_id=projectId)
    print("Analyzing %s tasks" % len(tasks))
    for task in tasks:
        sql = text(
            '''select * from webhook where project_id=:project_id and payload@>'{"task_id": :task_id}';''')
        results = db.engine.execute(
            sql, project_id=project.id, task_id=task.id)
        webhook = None
        for result in results:
            webhook = result
        if not webhook:
            result = result_repo.get_by(project_id=project.id, task_id=task.id)
            payload = dict(
                fired_at=None,
                project_short_name=project.short_name,
                project_id=project.id,
                task_id=task.id,
                result_id=result.id,
                event='task_completed')
            wh = Webhook(project_id=projectId,
                         payload=payload)
            print(wh)
            db.session.add(wh)
            db.session.commit()
    print("Project %s completed!" % project.short_name)


def create_results():
    """Create results when migrating."""
    from pybossa.core import project_repo, task_repo, result_repo
    from pybossa.model.result import Result

    projects = project_repo.filter_by(published=True)

    for project in projects:
        print("Working on project: %s" % project.short_name)
        tasks = task_repo.filter_tasks_by(state='completed',
                                          project_id=project.id)
        print("Analyzing %s tasks" % len(tasks))
        for task in tasks:
            result = result_repo.get_by(project_id=project.id, task_id=task.id)
            if result is None:
                result = Result(project_id=project.id,
                                task_id=task.id,
                                task_run_ids=[tr.id for tr in task.task_runs],
                                last_version=True)
                db.session.add(result)
        db.session.commit()
        print("Project %s completed!" % project.short_name)


def update_project_stats():
    """Update project stats for draft projects."""
    from pybossa.core import db
    from pybossa.core import project_repo, task_repo, result_repo
    from pybossa.model.task import Task
    from pybossa.model.task_run import TaskRun
    from pybossa.model.counter import Counter
    import pybossa.cache.project_stats as stats

    projects = project_repo.filter_by(published=False)

    for project in projects:
        print("Working on project: %s" % project.short_name)
        sql_query = """INSERT INTO project_stats 
                       (project_id, n_tasks, n_task_runs, n_results, n_volunteers,
                       n_completed_tasks, overall_progress, average_time,
                       n_blogposts, last_activity, info)
                       VALUES (%s, 0, 0, 0, 0, 0, 0, 0, 0, 0, '{}');""" % (project.id)
        db.engine.execute(sql_query)


def update_counters():
    """Populates the counters table."""
    from pybossa.core import db
    from pybossa.core import project_repo, task_repo, result_repo
    from pybossa.model.task import Task
    from pybossa.model.task_run import TaskRun
    from pybossa.model.counter import Counter

    projects = project_repo.get_all()

    print(len(projects))

    db.session.query(Counter).delete()
    db.session.commit()

    for project in projects:
        print("Working on project: %s" % project.id)
        sql = text('''select task.project_id as project_id, task.id as task_id, count(task_run.task_id) as n_task_runs from task left outer join task_run on (task_run.task_id=task.id) where task.project_id=:project_id group by task.project_id, task.id, task_run.task_id''')
        results = db.engine.execute(sql, project_id=project.id)
        for result in results:
            db.session.add(Counter(project_id=result.project_id,
                                   task_id=result.task_id,
                                   n_task_runs=result.n_task_runs))
        db.session.commit()


def update_project_stats():
    """Update project stats for draft projects."""
    from pybossa.core import db
    from pybossa.core import project_repo, task_repo, result_repo
    from pybossa.model.task import Task
    from pybossa.model.task_run import TaskRun
    from pybossa.model.counter import Counter
    import pybossa.cache.project_stats as stats

    projects = project_repo.get_all()

    for project in projects:
        print("Working on project: %s" % project.short_name)
        sql_query = """INSERT INTO project_stats 
                       (project_id, n_tasks, n_task_runs, n_results, n_volunteers,
                       n_completed_tasks, overall_progress, average_time,
                       n_blogposts, last_activity, info)
                       VALUES (%s, 0, 0, 0, 0, 0, 0, 0, 0, 0, '{}');""" % (project.id)
        db.engine.execute(sql_query)


def anonymize_ips():
    """Anonymize all the IPs of the server."""
    from pybossa.core import anonymizer, task_repo

    taskruns = task_repo.filter_task_runs_by(user_id=None)
    for tr in taskruns:
        print("Working on taskrun %s" % tr.id)
        print("From %s to %s" % (tr.user_ip, anonymizer.ip(tr.user_ip)))
        tr.user_ip = anonymizer.ip(tr.user_ip)
        task_repo.update(tr)


def clean_project(project_id, skip_tasks=False):
    """Remove everything from a project."""
    from pybossa.core import task_repo
    from pybossa.model import make_timestamp
    n_tasks = 0
    if not skip_tasks:
        print("Deleting tasks")
        sql = 'delete from task where project_id=%s' % project_id
        db.engine.execute(sql)
    else:
        sql = 'select count(id) as n from task where project_id=%s' % project_id
        result = db.engine.execute(sql)
        for row in result:
            n_tasks = row.n

    sql = 'delete from task_run where project_id=%s' % project_id
    db.engine.execute(sql)
    sql = 'delete from result where project_id=%s' % project_id
    db.engine.execute(sql)
    sql = 'delete from counter where project_id=%s' % project_id
    db.engine.execute(sql)
    sql = 'delete from project_stats where project_id=%s' % project_id
    db.engine.execute(sql)
    sql = """INSERT INTO project_stats 
             (project_id, n_tasks, n_task_runs, n_results, n_volunteers,
             n_completed_tasks, overall_progress, average_time,
             n_blogposts, last_activity, info)
             VALUES (%s, %s, 0, 0, 0, 0, 0, 0, 0, 0, '{}');""" % (project_id,
                                                                  n_tasks)
    db.engine.execute(sql)
    if skip_tasks:
        tasks = task_repo.filter_tasks_by(project_id=project_id, limit=100)
        last_id = tasks[len(tasks)-1].id
        while(len(tasks) > 0):
            for task in tasks:
                sql = ("insert into counter(created, project_id, task_id, n_task_runs) \
                       VALUES (TIMESTAMP '%s', %s, %s, 0)"
                       % (make_timestamp(), project_id, task.id))
                db.engine.execute(sql)
            tasks = task_repo.filter_tasks_by(project_id=project_id,
                                              limit=100,
                                              last_id=last_id)
            if (len(tasks) > 0):
                last_id = tasks[len(tasks)-1].id
    print("Project has been cleaned")


# ==================================================
# Misc stuff for setting up a command line interface

def _module_functions(functions):
    local_functions = dict(functions)
    for k, v in list(local_functions.items()):
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
        ['%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name, m)
         in sorted(_methods.items())])
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


__all__ = ['_main']

if __name__ == '__main__':
    _main(locals())
