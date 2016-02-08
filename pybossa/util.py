# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
"""Module with PyBossa utils."""
from datetime import timedelta, datetime
from functools import update_wrapper
import csv
import codecs
import cStringIO
from flask import abort, request, make_response, current_app
from functools import wraps
from flask.ext.login import current_user
from math import ceil
import json


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


# Fromhttp://stackoverflow.com/q/1551382
def pretty_date(time=False):
    """Return a pretty date.

    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc.
    """
    import dateutil.parser
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
    return dict(user_id=user_id, user_ip=user_ip)


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
        if not ('test' in project['name'].lower()
                or 'test' in project['short_name'].lower()):
            points += 500
        if project['info'].get('thumbnail'):
            points += 200
        points += _points_by_interval(project['n_tasks'], weight=1)
        points += _points_by_interval(project['n_volunteers'], weight=2)
        points += _last_activity_points(project)
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
