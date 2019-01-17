# -*- coding: utf8 -*-
SERVER_NAME='localhost'
PREFERRED_URL_SCHEME='https'
# THEME='pybossa-default-theme'
CRYPTOPAN_KEY = '32-char-str-for-AES-key-and-pad.'
SECRET = 'foobar'
SECRET_KEY = 'my-session-secret'
SQLALCHEMY_DATABASE_TEST_URI = 'postgresql://rtester:rtester@localhost/pybossa_test'
GOOGLE_CLIENT_ID = 'id'
GOOGLE_CLIENT_SECRET = 'secret'
TWITTER_CONSUMER_KEY='key'
TWITTER_CONSUMER_SECRET='secret'
FACEBOOK_APP_ID='id'
FACEBOOK_APP_SECRET='secret'
TERMSOFUSE = 'http://okfn.org/terms-of-use/'
DATAUSE = 'http://opendatacommons.org/licenses/by/'
ITSDANGEROUSKEY = 'its-dangerous-key'
REDIS_SOCKET_TIMEOUT = 1.0
LOGO = 'logo.png'
PORT=5001
MAIL_SERVER = 'localhost'
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_PORT = 25
MAIL_FAIL_SILENTLY = False
MAIL_DEFAULT_SENDER = 'PYBOSSA Support <info@pybossa.com>'
ADMINS = ['admin@broken.com']
ANNOUNCEMENT = {'admin': 'Root Message', 'user': 'User Message', 'owner': 'Owner Message'}
LOCALES = [('en', 'English'), ('es', u'Español'),
           ('it', 'Italiano'), ('fr', u'Français'),
           ('ja', u'日本語'), ('el', u'ελληνικά')]
ENFORCE_PRIVACY = False
REDIS_CACHE_ENABLED = False
REDIS_SENTINEL = [('localhost', 26379)]
REDIS_KEYPREFIX = 'pybossa_cache'
WTF_CSRF_ENABLED = False
WTF_CSRF_SSL_STRICT = False
TESTING = True
CSRF_ENABLED = False
MAIL_SERVER = 'localhost'
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_PORT = 25
MAIL_FAIL_SILENTLY = False
MAIL_DEFAULT_SENDER = 'PYBOSSA Support <info@pybossa.com>'
ALLOWED_EXTENSIONS = ['js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'zip']
UPLOAD_FOLDER = '/tmp/'
UPLOAD_METHOD = 'local'
RACKSPACE_USERNAME = 'username'
RACKSPACE_API_KEY = 'apikey'
RACKSPACE_REGION = 'ORD'
FLICKR_API_KEY = 'apikey'
FLICKR_SHARED_SECRET = "secret"
DROPBOX_APP_KEY = 'key'
YOUTUBE_API_SERVER_KEY = 'apikey'
LIMIT = 25
PER = 15 * 60
SSE = True
TIMEOUT = 5 * 60
LDAP_USER_OBJECT_FILTER = '(&(objectclass=inetOrgPerson)(cn=%s))'
LDAP_USER_FILTER_FIELD = 'cn'
LDAP_PYBOSSA_FIELDS = {'fullname': 'givenName',
                       'name': 'uid',
                       'email_addr': 'cn'}
FLASK_PROFILER = {
    "enabled": True,
    "storage": {
        "engine": "sqlite"
    },
    "basicAuth":{
        "enabled": True,
        "username": "admin",
        "password": "admin"
    },
    "ignore": [
	    "^/static/.*"
	]
}
AVATAR_ABSOLUTE = True
SPAM = ['fake.com']
USER_INACTIVE_NOTIFICATION = 5
USER_INACTIVE_DELETE = 6
