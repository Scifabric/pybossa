# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from datetime import timedelta
from functools import update_wrapper
import csv
import codecs
import cStringIO
from flask import abort, request, make_response, current_app
from functools import wraps
from flask_oauth import OAuth
from flaskext.login import current_user
from math import ceil
import json


def jsonpify(f):
    """Wraps JSONified output for JSONP"""
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


def admin_required(f):
    """Checks if the user is and admin or not"""
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
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):

        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
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


# From http://stackoverflow.com/q/1551382
def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    import dateutil.parser
    now = datetime.now()
    time = dateutil.parser.parse(time)
    if type(time) is int:
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

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=0, left_current=2, right_current=3,
                   right_edge=0):
        last = 0
        for num in xrange(1, self.pages + 1):
            if (num <= left_edge or
                    (num > self.page - left_current - 1 and
                     num < self.page + right_current) or
                    num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num


class Twitter:
    oauth = OAuth()

    def __init__(self, c_k, c_s):
        #oauth = OAuth()
        # Use Twitter as example remote application
        self.oauth = self.oauth.remote_app(
            'twitter',
            # unless absolute urls are used to make requests,
            # this will be added before all URLs. This is also true for
            # request_token_url and others.
            base_url='https://api.twitter.com/1/',
            # where flask should look for new request tokens
            request_token_url='https://api.twitter.com/oauth/request_token',
            # where flask should exchange the token with the remote application
            access_token_url='https://api.twitter.com/oauth/access_token',
            # twitter knows two authorizatiom URLs. /authorize and
            # /authenticate. They mostly work the same, but for sign
            # on /authenticate is expected because this will give
            # the user a slightly different
            # user interface on the twitter side.
            authorize_url='https://api.twitter.com/oauth/authenticate',
            # the consumer keys from the twitter application registry.
            consumer_key=c_k,  # app.config['TWITTER_CONSUMER_KEY'],
            consumer_secret=c_s)  # app.config['TWITTER_CONSUMER_KEY']


class Facebook:
    oauth = OAuth()

    def __init__(self, c_k, c_s):
        self.oauth = self.oauth.remote_app(
            'facebook',
            base_url='https://graph.facebook.com/',
            request_token_url=None,
            access_token_url='/oauth/access_token',
            authorize_url='https://www.facebook.com/dialog/oauth',
            consumer_key=c_k,  # app.config['FACEBOOK_APP_ID'],
            consumer_secret=c_s,  # app.config['FACEBOOK_APP_SECRET']
            request_token_params={'scope': 'email'})


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # This code is taken from http://docs.python.org/library/csv.html#examples
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    # This code is taken from http://docs.python.org/library/csv.html#examples
    for line in unicode_csv_data:
        yield line.encode('utf-8')


class Google:
    oauth = OAuth()

    def __init__(self, c_k, c_s):
        self.oauth = self.oauth.remote_app(
            'google',
            base_url='https://www.google.com/accounts/',
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            request_token_url=None,
            request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
                                  'response_type': 'code'},
            access_token_url='https://accounts.google.com/o/oauth2/token',
            access_token_method='POST',
            access_token_params={'grant_type': 'authorization_code'},
            consumer_key=c_k,
            consumer_secret=c_s)


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
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

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def get_user_signup_method(user):
    """Return which OAuth sign up method the user used"""
    msg = u'Sorry, there is already an account with the same e-mail.'
    print type(user.info)
    print user.info
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
