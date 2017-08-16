# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
"""Module with PyBossa utils."""
from collections import OrderedDict
from datetime import timedelta, datetime, date
from functools import update_wrapper
from flask_wtf import Form
import csv
import codecs
import cStringIO
import dateutil.tz
from flask import abort, request, make_response, current_app, url_for
from flask import redirect, render_template, jsonify, get_flashed_messages
from flask_wtf.csrf import generate_csrf
import dateutil.parser
from flask import abort, request, make_response, current_app
from functools import wraps
from flask.ext.login import current_user
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from math import ceil
import json
import base64
import hashlib
import hmac
import simplejson
import time
import pycountry
from flask.ext.babel import lazy_gettext
import re


def last_flashed_message():
    """Return last flashed message by flask."""
    messages = get_flashed_messages(with_categories=True)
    if len(messages) > 0:
        return messages[-1]
    else:
        return None


def form_to_json(form):
    """Return a form in JSON format."""
    tmp = form.data
    tmp['errors'] = form.errors
    tmp['csrf'] = generate_csrf()
    return tmp

def user_to_json(user):
    """Return a user in JSON format."""
    return user.dictize()

def handle_content_type(data):
    """Return HTML or JSON based on request type."""
    from pybossa.model.project import Project
    if request.headers.get('Content-Type') == 'application/json':
        message_and_status = last_flashed_message()
        if message_and_status:
            data['flash'] = message_and_status[1]
            data['status'] = message_and_status[0]
        for item in data.keys():
            if isinstance(data[item], Form):
                data[item] = form_to_json(data[item])
            if isinstance(data[item], Pagination):
                data[item] = data[item].to_json()
            if (item == 'announcements'):
                data[item] = [announcement.to_public_json() for announcement in data[item]]
            if (item == 'blogposts'):
                data[item] = [blog.to_public_json() for blog in data[item]]
            if (item == 'categories'):
                tmp = []
                for cat in data[item]:
                    if type(cat) != dict:
                        cat = cat.to_public_json()
                    tmp.append(cat)
                data[item] = tmp
            if (item == 'active_cat'):
                if type(data[item]) != dict:
                    cat = data[item].to_public_json()
                data[item] = cat
            if (item == 'users') and type(data[item]) != str:
                data[item] = [user_to_json(user) for user in data[item]]
            if (item == 'users' or item =='projects' or item == 'tasks' or item == 'locs') and type(data[item]) == str:
                data[item] = json.loads(data[item])
            if (item == 'found'):
                data[item] = [user_to_json(user) for user in data[item]]
            if (item == 'category'):
                data[item] = data[item].to_public_json()

        if 'code' in data.keys():
            return jsonify(data), data['code']
        else:
            return jsonify(data)
    else:
        template = data['template']
        del data['template']
        if 'code' in data.keys():
            error_code = data['code']
            del data['code']
            return render_template(template, **data), error_code
        else:
            return render_template(template, **data)

def redirect_content_type(url, status=None):
    data = dict(next=url)
    if status is not None:
        data['status'] = status
    if request.headers.get('Content-Type') == 'application/json':
        return handle_content_type(data)
    else:
        return redirect(url)


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


def jsonpify(f):
    """Wrap JSONified output for JSONP."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args, **kwargs).data) + ')'
            return current_app.response_class(content,
                                              mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function


def admin_required(f):  # pragma: no cover
    """Check if the user is and admin or not."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.admin:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


def admin_or_subadmin_required(f):  # pragma: no cover
    """Check if the user is and admin or not."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.admin or current_user.subadmin:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


# from http://flask.pocoo.org/snippets/56/
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """Crossdomain decorator."""
    if methods is not None:  # pragma: no cover
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):  # pragma: no cover
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):  # pragma: no cover
        max_age = max_age.total_seconds()

    def get_methods():  # pragma: no cover
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):

        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':  # pragma: no cover
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':  # pragma: no cover
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def parse_date_string(source):
    if not isinstance(source, (date, datetime)):
        try:
            return dateutil.parser.parse(str(source))
        except:
            return source

    return source


def convert_est_to_utc(source):
    source = parse_date_string(source)

    utc = dateutil.tz.gettz('UTC')
    est = dateutil.tz.gettz('America/New_York')

    # naive to EST to UTC
    return source.replace(tzinfo=est).astimezone(utc)


def convert_utc_to_est(source):
    source = parse_date_string(source)

    utc = dateutil.tz.gettz('UTC')
    est = dateutil.tz.gettz('America/New_York')

    # naive to UTC to EST
    return source.replace(tzinfo=utc).astimezone(est)


# From http://stackoverflow.com/q/1551382
def pretty_date(time=False):
    """Return a pretty date.

    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc.
    """
    now = datetime.now()
    if type(time) is str or type(time) is unicode:
        time = dateutil.parser.parse(time)
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    if type(time) is float:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return ' '.join([str(second_diff / 60), "minutes ago"])
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return ' '.join([str(second_diff / 3600), "hours ago"])
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return ' '.join([str(day_diff), "days ago"])
    if day_diff < 31:
        return ' '.join([str(day_diff / 7), "weeks ago"])
    if day_diff < 60:
        return ' '.join([str(day_diff / 30), "month ago"])
    if day_diff < 365:
        return ' '.join([str(day_diff / 30), "months ago"])
    if day_diff < (365 * 2):
        return ' '.join([str(day_diff / 365), "year ago"])
    return ' '.join([str(day_diff / 365), "years ago"])


def datetime_filter(source, fmt):

    if not isinstance(source, (date, datetime)):
        try:
            source = datetime.strptime(str(source), "%Y-%m-%dT%H:%M:%S.%f")
        except Exception:
            return source

    utc = dateutil.tz.gettz('UTC')
    est = dateutil.tz.gettz('America/New_York')

    # naive to UTC to local
    source = source.replace(tzinfo=utc).astimezone(est)
    return source.strftime(fmt)


class Pagination(object):

    """Class to paginate domain objects."""

    def __init__(self, page, per_page, total_count):
        """Init method."""
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        """Return number of pages."""
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        """Return if it has a previous page."""
        return self.page > 1

    @property
    def has_next(self):
        """Return if it has a next page."""
        return self.page < self.pages

    def iter_pages(self, left_edge=0, left_current=2, right_current=3,
                   right_edge=0):
        """Iterate over pages."""
        last = 0
        for num in xrange(1, self.pages + 1):
            if (num <= left_edge or
                    (num > self.page - left_current - 1 and
                     num < self.page + right_current) or
                    num > self.pages - right_edge):
                if last + 1 != num:  # pragma: no cover
                    yield None
                yield num
                last = num

    def to_json(self):
        """Return the object in JSON format."""
        return dict(page=self.page,
                    per_page=self.per_page,
                    total=self.total_count,
                    next=self.has_next,
                    prev=self.has_prev)


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    """Unicode CSV reader."""
    # This code is taken from http://docs.python.org/library/csv.html#examples
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    """UTF8 encoder for CSV data."""
    # This code is taken from http://docs.python.org/library/csv.html#examples
    for line in unicode_csv_data:
        yield line.encode('utf-8')


class UnicodeWriter:

    """A CSV writer which will write rows to CSV file "f"."""

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        """Init method."""
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        """Write row."""
        line = []
        for s in row:
            if (type(s) == dict):
                line.append(json.dumps(s))
            else:
                line.append(unicode(s).encode("utf-8"))
        self.writer.writerow(line)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):  # pragma: no cover
        """Write rows."""
        for row in rows:
            self.writerow(row)


def get_user_signup_method(user):
    """Return which OAuth sign up method the user used."""
    msg = u'Sorry, there is already an account with the same e-mail.'
    if user.info:
        # Google
        if user.info.get('google_token'):
            msg += " <strong>It seems like you signed up with your Google account.</strong>"
            msg += "<br/>You can try and sign in by clicking in the Google button."
            return (msg, 'google')
        # Facebook
        elif user.info.get('facebook_token'):
            msg += " <strong>It seems like you signed up with your Facebook account.</strong>"
            msg += "<br/>You can try and sign in by clicking in the Facebook button."
            return (msg, 'facebook')
        # Twitter
        elif user.info.get('twitter_token'):
            msg += " <strong>It seems like you signed up with your Twitter account.</strong>"
            msg += "<br/>You can try and sign in by clicking in the Twitter button."
            return (msg, 'twitter')
        # Local account
        else:
            msg += " <strong>It seems that you created an account locally.</strong>"
            msg += " <br/>You can reset your password if you don't remember it."
            return (msg, 'local')
    else:
        msg += " <strong>It seems that you created an account locally.</strong>"
        msg += " <br/>You can reset your password if you don't remember it."
        return (msg, 'local')


def get_port():
    """Get port."""
    import os
    port = os.environ.get('PORT', '')
    if port.isdigit():
        return int(port)
    else:
        return current_app.config['PORT']


def get_user_id_or_ip():
    """Return the id of the current user if is authenticated.
    Otherwise returns its IP address (defaults to 127.0.0.1).
    """
    user_id = current_user.id if current_user.is_authenticated() else None
    user_ip = request.remote_addr or "127.0.0.1" \
        if current_user.is_anonymous() else None
    external_uid = request.args.get('external_uid')
    return dict(user_id=user_id, user_ip=user_ip, external_uid=external_uid)


def with_cache_disabled(f):
    """Decorator that disables the cache for the execution of a function.
    It enables it back when the function call is done.
    """
    import os

    @wraps(f)
    def wrapper(*args, **kwargs):
        env_cache_disabled = os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')
        if env_cache_disabled is None or env_cache_disabled is '0':
            os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'
        return_value = f(*args, **kwargs)
        if env_cache_disabled is None:
            del os.environ['PYBOSSA_REDIS_CACHE_DISABLED']
        else:
            os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = env_cache_disabled
        return return_value
    return wrapper


def is_reserved_name(blueprint, name):
    """Check if a name has already been registered inside a blueprint URL."""
    path = ''.join(['/', blueprint])
    app_urls = [r.rule for r in current_app.url_map.iter_rules()
                if r.rule.startswith(path)]
    reserved_names = [url.split('/')[2] for url in app_urls
                      if url.split('/')[2] != '']
    return name in reserved_names


def username_from_full_name(username):
    """Takes a username that may contain several words with capital letters and
    returns a single word username, no spaces, all lowercases."""
    if type(username) == str:
        return username.decode('ascii', 'ignore').lower().replace(' ', '')
    return username.encode('ascii', 'ignore').decode('utf-8').lower().replace(' ', '')


def rank(projects):
    """Takes a list of (published) projects (as dicts) and orders them by
    activity, number of volunteers, number of tasks and other criteria."""
    def earned_points(project):
        points = 0
        if project['overall_progress'] != 100L:
            points += 1000
        points += _points_by_interval(project['n_tasks'], weight=1)
        points += _points_by_interval(project['n_volunteers'], weight=2)
        points += _last_activity_points(project) * 10
        return points

    projects.sort(key=earned_points, reverse=True)
    return projects


def _last_activity_points(project):
    default = datetime(1970, 1, 1, 0, 0).strftime('%Y-%m-%dT%H:%M:%S')
    updated_datetime = (project.get('updated') or default)
    last_activity_datetime = (project.get('last_activity_raw') or default)
    updated_datetime = updated_datetime.split('.')[0]
    last_activity_datetime = last_activity_datetime.split('.')[0]
    updated = datetime.strptime(updated_datetime, '%Y-%m-%dT%H:%M:%S')
    last_activity = datetime.strptime(last_activity_datetime, '%Y-%m-%dT%H:%M:%S')
    most_recent = max(updated, last_activity)

    days_since_modified = (datetime.utcnow() - most_recent).days

    if days_since_modified < 1:
        return 50
    if days_since_modified < 2:
        return 20
    if days_since_modified < 3:
        return 10
    if days_since_modified < 4:
        return 5
    if days_since_modified > 15:
        return -200
    return 0


def _points_by_interval(value, weight=1):
    if value > 100:
        return 20 * weight
    if value > 50:
        return 15 * weight
    if value > 20:
        return 10 * weight
    if value > 10:
        return 5 * weight
    if value > 0:
        return 1 * weight
    return 0


def publish_channel(sentinel, project_short_name, data, type, private=True):
    """Publish in a channel some JSON data as a string."""
    if private:
        channel = "channel_%s_%s" % ("private", project_short_name)
    else:
        channel = "channel_%s_%s" % ("public", project_short_name)
    msg = dict(type=type, data=data)
    sentinel.master.publish(channel, json.dumps(msg))


# See https://github.com/flask-restful/flask-restful/issues/332#issuecomment-63155660
def fuzzyboolean(value):
    if type(value) == bool:
        return value

    if not value:
        raise ValueError("boolean type must be non-null")
    value = value.lower()
    if value in ('false', 'no', 'off', 'n', '0',):
        return False
    if value in ('true', 'yes', 'on', 'y', '1',):
        return True
    raise ValueError("Invalid literal for boolean(): {}".format(value))


def get_avatar_url(upload_method, avatar, container):
    """Return absolute URL for avatar."""
    if upload_method.lower() == 'rackspace':
        return url_for('rackspace',
                       filename=avatar,
                       container=container)
    else:
        filename = container + '/' + avatar
        return url_for('uploads.uploaded_file', filename=filename)


def get_disqus_sso(user): # pragma: no cover
    # create a JSON packet of our data attributes
    # return a script tag to insert the sso message."""
    message, timestamp, sig, pub_key = get_disqus_sso_payload(user)
    return """<script type="text/javascript">
    var disqus_config = function() {
        this.page.remote_auth_s3 = "%(message)s %(sig)s %(timestamp)s";
        this.page.api_key = "%(pub_key)s";
    }
    </script>""" % dict(
        message=message,
        timestamp=timestamp,
        sig=sig,
        pub_key=pub_key,
    )


def get_disqus_sso_payload(user):
    """Return remote_auth_s3 and api_key for user."""
    DISQUS_PUBLIC_KEY = current_app.config.get('DISQUS_PUBLIC_KEY')
    DISQUS_SECRET_KEY = current_app.config.get('DISQUS_SECRET_KEY')
    if DISQUS_PUBLIC_KEY and DISQUS_SECRET_KEY:
        if user:
            data = simplejson.dumps({
                'id': user.id,
                'username': user.name,
                'email': user.email_addr,
            })
        else:
            data = simplejson.dumps({})
        # encode the data to base64
        message = base64.b64encode(data)
        # generate a timestamp for signing the message
        timestamp = int(time.time())
        # generate our hmac signature
        sig = hmac.HMAC(DISQUS_SECRET_KEY, '%s %s' % (message, timestamp),
                        hashlib.sha1).hexdigest()

        return message, timestamp, sig, DISQUS_PUBLIC_KEY
    else:
        return None, None, None, None


def exists_materialized_view(db, view):
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname = :view);''')
    results = db.slave_session.execute(sql, dict(view=view))
    for result in results:
        return result.exists
    return False


def refresh_materialized_view(db, view):
    try:
        sql = text('REFRESH MATERIALIZED VIEW CONCURRENTLY %s' % view)
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view refreshed concurrently"
    except ProgrammingError:
        sql = text('REFRESH MATERIALIZED VIEW %s' % view)
        db.session.rollback()
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view refreshed"


def generate_invitation_email_for_new_user(user, project_slugs=None):
    project_slugs = project_slugs or []
    server_url = current_app.config.get('SERVER_URL')
    user_manual_label = current_app.config.get('USER_MANUAL_LABEL')
    user_manual_url = current_app.config.get('USER_MANUAL_URL')
    brand = current_app.config.get('BRAND')
    project_urls = []
    for project_slug in project_slugs:
        project_url = None if not project_slug else server_url + '/project/' + project_slug
        if project_url:
            project_urls.append(project_url)
    bcc = []
    if current_user.is_authenticated():
        bcc.append(current_user.email_addr)
    msg = dict(subject='New account with {}'.format(brand),
               recipients=[user['email_addr']],
               bcc=bcc)
    msg['html'] = render_template('/account/email/newaccount_invite.html',
                                  user=user, project_urls=project_urls,
                                  user_manual_label=user_manual_label,
                                  user_manual_url=user_manual_url,
                                  server_url=server_url)
    return msg


def generate_invitation_email_for_admins_subadmins(user, access_type):
    if not user or not access_type:
        return None

    server_url = current_app.config.get('SERVER_URL')
    admin_manual_label = current_app.config.get('ADMIN_MANUAL_LABEL')
    admin_manual_url = current_app.config.get('ADMIN_MANUAL_URL')
    brand = current_app.config.get('BRAND')
    msg = dict(subject='Account access update on {}'.format(brand),
               recipients=[user.email_addr],
               bcc=[current_user.email_addr])
    msg['html'] = render_template('/account/email/adminsubadmin_invite.html',
                                  username=user.fullname,
                                  access_type=access_type,
                                  admin_manual_label=admin_manual_label,
                                  admin_manual_url=admin_manual_url,
                                  server_url=server_url)
    return msg


def generate_manage_user_email(user, operation):
    if not user or not operation:
        return None

    brand = current_app.config.get('BRAND')
    server_url = current_app.config.get('SERVER_URL')

    if operation == 'enable':
        msg_header = '{} Account Enabled'.format(brand)
        msg_text = 'Your account {0} with {1} at {2} has been enabled. '\
                   'You can now login with your account credentials.'\
                   .format(user.email_addr, brand, server_url)

    elif operation == 'disable':
        msg_header = '{} Account Disabled'.format(brand)
        msg_text = 'Your account {0} with {1} at {2} has been disabled. '\
                   'Please contact your {1} administrator about reinstating your account.'\
                   .format(user.email_addr, brand, server_url)
    else:
        return None

    if current_app.config.get('IS_QA'):
        msg_header = msg_header + ' (QA Version)'

    msg = dict(subject='Account update on {}'.format(brand),
               recipients=[user.email_addr],
               bcc=[current_user.email_addr])
    msg['html'] = render_template('/account/email/manageuser.html',
                                  username=user.fullname,
                                  msgHeader=msg_header,
                                  msgText=msg_text)
    return msg


class AttrDict(OrderedDict):
    def __getattr__(self, name):
        if not name.startswith('_'):
            return self[name]
        return super(AttrDict, self).__getattr__(name)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            self[name] = value
        else:
            super(AttrDict, self).__setattr__(name, value)

    def dictize(self):
        return self


def timezones():
    tz = [("", ""), ("ACT", "Australia Central Time"),
        ("AET", "Australia Eastern Time"),
        ("AGT", "Argentina Standard Time"),
        ("ART", "(Arabic) Egypt Standard Time"),
        ("AST", "Alaska Standard Time"),
        ("BET", "Brazil Eastern Time"),
        ("BST", "Bangladesh Standard Time"),
        ("CAT", "Central African Time"),
        ("CNT", "Canada Newfoundland Time"),
        ("CST", "Central Standard Time"),
        ("CTT", "China Taiwan Time"),
        ("EAT", "Eastern African Time"),
        ("ECT", "European Central Time"),
        ("EET", "Eastern European Time"),
        ("EST", "Eastern Standard Time"),
        ("GMT", "Greenwich Mean Time"),
        ("HST", "Hawaii Standard Time"),
        ("IET", "Indiana Eastern Standard Time"),
        ("IST", "India Standard Time"),
        ("JST", "Japan Standard Time"),
        ("MET", "Middle East Time"),
        ("MIT", "Midway Islands Time"),
        ("MST", "Mountain Standard Time"),
        ("NET", "Near East Time"),
        ("NST", "New Zealand Standard Time"),
        ("PLT", "Pakistan Lahore Time"),
        ("PNT", "Phoenix Standard Time"),
        ("PRT", "Puerto Rick and US Virgin Islands Time"),
        ("PST", "Pacific Standard Time"),
        ("SST", "Solomon Standard Time"),
        ("UTC", "Universal Coordinated Time"),
        ("VST", "Vietnam Standard Time")]
    return tz


def user_types():
    types = [("", ""),
        ("Temporary Employee", "Temporary Employee"),
        ("Intern", "Intern"),
        ("Full-time Employee", "Full-time Employee"),
        ("Part-time Employee", "Part-time Employee"),
        ("Vendor", "Vendor"),
        ("Freelancer", "Freelancer"),
        ("Subcontractor", "Subcontractor")]
    return types


def languages():
    langs = [("English", "English"),
        ("Arabic", "Arabic"),
        ("Bengali", "Bengali"),
        ("Chinese", "Chinese"),
        ("French", "French"),
        ("German", "German"),
        ("Hindi", "Hindi"),
        ("Italian", "Italian"),
        ("Japanese", "Japanese"),
        ("Korean", "Korean"),
        ("Portuguese", "Portuguese"),
        ("Russian", "Russian"),
        ("Spanish", "Spanish")]
    return langs


def countries():
    cts = []
    for ct in pycountry.countries:
        name = ct.name.encode('ascii', 'ignore').replace("'", "")
        cts.append((name, name))
    return sorted(cts)


def check_password_strength(
        password, min_len=8, max_len=15,
        uppercase=True, lowercase=True,
        numeric=True, special=True, message=""):
    """Check password strength, return True if passed.
    Otherwise return False with exact failure message.
    """

    required_chars = []
    if uppercase:
        required_chars.append(r'[A-Z]')
    if lowercase:
        required_chars.append(r'[a-z]')
    if numeric:
        required_chars.append(r'[0-9]')
    if special:
        required_chars.append(r'[!@$%^&*#]')

    pwd_len = len(password)
    if pwd_len < min_len or pwd_len > max_len:
        message = lazy_gettext(
                    u'Password must be between {0} and {1} characters'
                    .format(min_len, max_len))
        return False, message

    valid = all(re.search(ch, password) for ch in required_chars)
    if not valid:
        return False, message
    else:
        return True, None


def get_s3_bucket_name(url):
    # for 'http://bucket.s3.amazonaws.com/
    found = re.search('^https?://([^.]+).s3.amazonaws.com', url)
    if found:
        return found.group(1)
    # for 'http://s3.amazonaws.com/bucket'
    found = re.search('^https?://s3.amazonaws.com/([^\/]+)', url)
    if found:
        return found.group(1)
    return None


def valid_or_no_s3_bucket(task_data):
    """ Returns False when task has s3 url and s3 bucket is not cf-s3uploads"""
    allowed_s3_buckets = current_app.config.get('ALLOWED_S3_BUCKETS')

    # with no bucket configured, do not performing bucket check (default)
    if allowed_s3_buckets is None:
        return True

    for v in task_data.itervalues():
        bucket = get_s3_bucket_name(v)
        if bucket is not None and bucket not in allowed_s3_buckets:
            return False
    return True


def can_update_user_info(current_user, user_to_update):
    if current_user.admin:
        return True
    if not current_user.subadmin:
        return False
    return not (user_to_update.admin or user_to_update.subadmin)
