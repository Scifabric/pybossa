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
"""Module with PYBOSSA utils."""
import os

from yacryptopan import CryptoPAn
from datetime import timedelta, datetime
from functools import update_wrapper
from flask_wtf import Form
import csv
import codecs
import io
from flask import abort, request, make_response, current_app, url_for
from flask import redirect, render_template, jsonify, get_flashed_messages
from flask_wtf.csrf import generate_csrf
from functools import wraps
from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from math import ceil
import json
import base64
import hashlib
import hmac
import simplejson
import time
from flask_babel import lazy_gettext
import re
import pycountry


def redis_cache_is_enabled():
    return os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None


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


def hash_last_flash_message():
    """Base64 encode the last flash message"""
    data = {}
    message_and_status = last_flashed_message()
    if message_and_status:
        data['flash'] = message_and_status[1]
        data['status'] = message_and_status[0]
    json_data = json.dumps(data)
    return base64.b64encode(json_data.encode('utf-8'))


def handle_content_type(data):
    """Return HTML or JSON based on request type."""
    from pybossa.model.project import Project
    if (request.headers.get('Content-Type') == 'application/json' or
            request.args.get('response_format') == 'json'):
        message_and_status = last_flashed_message()
        if message_and_status:
            data['flash'] = message_and_status[1]
            data['status'] = message_and_status[0]
        for item in list(data.keys()):
            if isinstance(data[item], Form):
                data[item] = form_to_json(data[item])
            if isinstance(data[item], Pagination):
                data[item] = data[item].to_json()
            if (item == 'announcements'):
                data[item] = [announcement.to_public_json()
                              for announcement in data[item]]
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
            if (item == 'users' or item == 'projects' or item == 'tasks' or item == 'locs') and type(data[item]) == str:
                data[item] = json.loads(data[item])
            if (item == 'found'):
                data[item] = [user_to_json(user) for user in data[item]]
            if (item == 'category'):
                data[item] = data[item].to_public_json()

        if 'code' in list(data.keys()):
            return jsonify(data), data['code']
        else:
            return jsonify(data)
    else:
        template = data['template']
        del data['template']
        if 'code' in list(data.keys()):
            error_code = data['code']
            del data['code']
            return render_template(template, **data), error_code
        else:
            return render_template(template, **data)


def redirect_content_type(url, status=None):
    data = dict(next=url)
    if status is not None:
        data['status'] = status
    if (request.headers.get('Content-Type') == 'application/json' or
            request.args.get('response_format') == 'json'):
        return handle_content_type(data)
    else:
        return redirect(url)


def url_for_app_type(endpoint, _hash_last_flash=False, **values):
    """Generate a URL for an SPA, or otherwise."""
    spa_server_name = current_app.config.get('SPA_SERVER_NAME')
    if spa_server_name:
        values.pop('_external', None)
        values.pop('_scheme', None)
        if _hash_last_flash:
            values['flash'] = hash_last_flash_message()
            return spa_server_name + url_for(endpoint, **values)
        return spa_server_name + url_for(endpoint, **values)
    return url_for(endpoint, **values)


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


# Fromhttp://stackoverflow.com/q/1551382
def pretty_date(time=False):
    """Return a pretty date.

    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc.
    """
    import dateutil.parser
    now = datetime.now()
    if type(time) is str or type(time) is str:
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
            return ' '.join([str(int(second_diff / 60)), "minutes ago"])
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return ' '.join([str(int(second_diff / 3600)), "hours ago"])
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return ' '.join([str(int(day_diff)), "days ago"])
    if day_diff < 31:
        return ' '.join([str(int(day_diff / 7)), "weeks ago"])
    if day_diff < 60:
        return ' '.join([str(int(day_diff / 30)), "month ago"])
    if day_diff < 365:
        return ' '.join([str(int(day_diff / 30)), "months ago"])
    if day_diff < (365 * 2):
        return ' '.join([str(int(day_diff / 365)), "year ago"])
    return ' '.join([str(int(day_diff / 365)), "years ago"])


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
        for num in range(1, self.pages + 1):
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


def get_user_signup_method(user):
    """Return which OAuth sign up method the user used."""
    msg = 'Sorry, there is already an account with the same e-mail.'
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
    cp = CryptoPAn(str.encode(current_app.config.get('CRYPTOPAN_KEY')))
    user_id = current_user.id if current_user.is_authenticated else None
    user_ip = cp.anonymize(request.remote_addr or "127.0.0.1") \
        if current_user.is_anonymous else None
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
        if env_cache_disabled is None or env_cache_disabled == '0':
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
    username = username.replace(' ', '')
    username = username.lower()
    return username.encode('ascii', 'ignore')


def rank(projects, order_by=None, desc=False):
    """By default, takes a list of (published) projects (as dicts) and orders
    them by activity, number of volunteers, number of tasks and other criteria.

    Alternatively ranks by order_by and desc.
    """
    def earned_points(project):
        points = 0
        if project['overall_progress'] != 100:
            points += 1000
        if not ('test' in project['name'].lower()
                or 'test' in project['short_name'].lower()):
            points += 500
        if project['info'].get('thumbnail'):
            points += 200
        points += _points_by_interval(project['n_tasks'], weight=1)
        points += _points_by_interval(project['n_volunteers'], weight=2)
        points += _last_activity_points(project)
        return points

    if order_by:
        projects.sort(key=lambda x: x[str(order_by)], reverse=desc)
    else:
        projects.sort(key=earned_points, reverse=True)
    return projects


def _last_activity_points(project):
    default = datetime(1970, 1, 1, 0, 0).strftime('%Y-%m-%dT%H:%M:%S')
    updated_datetime = (project.get('updated') or default)
    last_activity_datetime = (project.get('last_activity_raw') or default)
    updated_datetime = updated_datetime.split('.')[0]
    last_activity_datetime = last_activity_datetime.split('.')[0]
    updated = datetime.strptime(updated_datetime, '%Y-%m-%dT%H:%M:%S')
    last_activity = datetime.strptime(
        last_activity_datetime, '%Y-%m-%dT%H:%M:%S')
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


def get_avatar_url(upload_method, avatar, container, external):
    """Return absolute URL for avatar."""
    if upload_method.lower() == 'rackspace':
        return url_for('rackspace',
                       filename=avatar,
                       container=container)
    else:
        filename = container + '/' + avatar
        return url_for('uploads.uploaded_file',
                       filename=filename,
                       _scheme=current_app.config.get('PREFERRED_URL_SCHEME'),
                       _external=external)


def get_disqus_sso(user):  # pragma: no cover
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
        message = base64.b64encode(data.encode('utf-8'))
        # generate a timestamp for signing the message
        timestamp = int(time.time())
        # generate our hmac signature
        tmp = '{} {}'.format(message, timestamp).encode('utf-8')
        sig = hmac.HMAC(DISQUS_SECRET_KEY.encode('utf-8'), tmp,
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
                    'Password must be between {0} and {1} characters'
                    .format(min_len, max_len))
        return False, message

    valid = all(re.search(ch, password) for ch in required_chars)
    if not valid:
        return False, message
    else:
        return True, None
