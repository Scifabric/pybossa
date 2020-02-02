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
"""Core module for PYBOSSA."""
import os
import logging
import humanize
from flask import Flask, url_for, request, render_template, \
    flash, _app_ctx_stack, abort, redirect
from flask_login import current_user
from flask_babel import gettext
from flask_assets import Bundle
from flask_json_multidict import get_json_multidict
from pybossa import default_settings as settings
from pybossa.extensions import *
from pybossa.ratelimit import get_view_rate_limit
from raven.contrib.flask import Sentry
from pybossa.util import pretty_date, handle_content_type, get_disqus_sso
from pybossa.news import FEED_KEY as NEWS_FEED_KEY
from pybossa.news import get_news
from pybossa.messages import *
from pybossa import util


def create_app(run_as_server=True):
    """Create web app."""
    app = Flask(__name__)
    configure_app(app)
    setup_assets(app)
    setup_cache_timeouts(app)
    setup_ratelimits(app)
    setup_theme(app)
    setup_uploader(app)
    setup_error_email(app)
    setup_logging(app)
    setup_login_manager(app)
    setup_babel(app)
    setup_markdown(app)
    setup_db(app)
    setup_repositories(app)
    setup_exporter(app)
    setup_strong_password(app)
    mail.init_app(app)
    sentinel.init_app(app)
    signer.init_app(app)
    if app.config.get('SENTRY_DSN'):  # pragma: no cover
        Sentry(app)
    if run_as_server:  # pragma: no cover
        setup_scheduled_jobs(app)
    setup_blueprints(app)
    setup_hooks(app)
    setup_error_handlers(app)
    setup_ldap(app)
    setup_external_services(app)
    setup_jinja(app)
    setup_csrf_protection(app)
    setup_debug_toolbar(app)
    setup_jinja2_filters(app)
    setup_newsletter(app)
    setup_sse(app)
    setup_json_serializer(app)
    setup_cors(app)
    setup_profiler(app)
    plugin_manager.init_app(app)
    plugin_manager.install_plugins()
    import pybossa.model.event_listeners
    setup_upref_mdata(app)
    anonymizer.init_app(app)
    return app


def configure_app(app):
    """Configure web app."""
    app.config.from_object(settings)
    app.config.from_envvar('PYBOSSA_SETTINGS', silent=True)
    # parent directory
    if not os.environ.get('PYBOSSA_SETTINGS'):  # pragma: no cover
        here = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(here), 'settings_local.py')
        if os.path.exists(config_path):  # pragma: no cover
            app.config.from_pyfile(config_path)
    else:
        config_path = os.path.abspath(os.environ.get('PYBOSSA_SETTINGS'))

    config_upref_mdata = os.path.join(
        os.path.dirname(config_path), 'settings_upref_mdata.py')
    app.config.upref_mdata = True if os.path.exists(
        config_upref_mdata) else False

    # Override DB in case of testing
    if app.config.get('SQLALCHEMY_DATABASE_TEST_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = \
            app.config['SQLALCHEMY_DATABASE_TEST_URI']
    # Enable Slave bind in case is missing using Master node
    if app.config.get('SQLALCHEMY_BINDS') is None:
        print("Slave binds are misssing, adding Master as slave too.")
        app.config['SQLALCHEMY_BINDS'] = \
            dict(slave=app.config.get('SQLALCHEMY_DATABASE_URI'))
    app.url_map.strict_slashes = app.config.get('STRICT_SLASHES')


def setup_json_serializer(app):
    app.json_encoder = JSONEncoder


def setup_cors(app):
    cors.init_app(app, resources=app.config.get('CORS_RESOURCES'))


def setup_sse(app):
    if app.config['SSE']:
        msg = "WARNING: async mode is required as Server Sent Events are enabled."
        app.logger.warning(msg)
    else:  # pragma: no cover
        msg = "INFO: async mode is disabled."
        app.logger.info(msg)


def setup_theme(app):
    """Configure theme for PYBOSSA app."""
    theme = app.config['THEME']
    app.template_folder = os.path.join('themes', theme, 'templates')
    app.static_folder = os.path.join('themes', theme, 'static')


def setup_uploader(app):
    """Setup uploader."""
    global uploader
    if app.config.get('UPLOAD_METHOD') == 'local':
        from pybossa.uploader.local import LocalUploader
        uploader = LocalUploader()
        uploader.init_app(app)
    if app.config.get('UPLOAD_METHOD') == 'rackspace':  # pragma: no cover
        from pybossa.uploader.rackspace import RackspaceUploader
        uploader = RackspaceUploader()
        app.url_build_error_handlers.append(uploader.external_url_handler)
        uploader.init_app(app)


def setup_exporter(app):
    """Setup exporter."""
    global csv_exporter
    global json_exporter
    from pybossa.exporter.csv_export import CsvExporter
    from pybossa.exporter.json_export import JsonExporter
    csv_exporter = CsvExporter()
    json_exporter = JsonExporter()


def setup_markdown(app):
    """Setup markdown."""
    misaka.init_app(app)


def setup_db(app):
    """Setup database."""
    def create_slave_session(db, bind):
        if (app.config.get('SQLALCHEMY_BINDS')['slave'] ==
                app.config.get('SQLALCHEMY_DATABASE_URI')):
            return db.session
        engine = db.get_engine(db.app, bind=bind)
        options = dict(bind=engine, scopefunc=_app_ctx_stack.__ident_func__)
        slave_session = db.create_scoped_session(options=options)
        return slave_session
    db.app = app
    db.init_app(app)
    db.slave_session = create_slave_session(db, bind='slave')
    if db.slave_session is not db.session:
        # flask-sqlalchemy does it already for default session db.session
        @app.teardown_appcontext
        def _shutdown_session(response_or_exc):  # pragma: no cover
            if app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']:
                if response_or_exc is None:
                    db.slave_session.commit()
            db.slave_session.remove()
            return response_or_exc


def setup_repositories(app):
    """Setup repositories."""
    from pybossa.repositories import UserRepository
    from pybossa.repositories import ProjectRepository
    from pybossa.repositories import ProjectStatsRepository
    from pybossa.repositories import AnnouncementRepository
    from pybossa.repositories import BlogRepository
    from pybossa.repositories import TaskRepository
    from pybossa.repositories import AuditlogRepository
    from pybossa.repositories import WebhookRepository
    from pybossa.repositories import ResultRepository
    from pybossa.repositories import HelpingMaterialRepository
    from pybossa.repositories import PageRepository
    global user_repo
    global project_repo
    global project_stats_repo
    global announcement_repo
    global blog_repo
    global task_repo
    global auditlog_repo
    global webhook_repo
    global result_repo
    global helping_repo
    global page_repo
    language = app.config.get('FULLTEXTSEARCH_LANGUAGE')
    user_repo = UserRepository(db)
    project_repo = ProjectRepository(db)
    project_stats_repo = ProjectStatsRepository(db)
    announcement_repo = AnnouncementRepository(db)
    blog_repo = BlogRepository(db)
    task_repo = TaskRepository(db, language)
    auditlog_repo = AuditlogRepository(db)
    webhook_repo = WebhookRepository(db)
    result_repo = ResultRepository(db)
    helping_repo = HelpingMaterialRepository(db)
    page_repo = PageRepository(db)


def setup_error_email(app):
    """Setup error email."""
    from logging.handlers import SMTPHandler
    ADMINS = app.config.get('ADMINS', '')
    if not app.debug and ADMINS:  # pragma: no cover
        mail_handler = SMTPHandler('127.0.0.1',
                                   'server-error@no-reply.com',
                                   ADMINS, 'error')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


def setup_logging(app):
    """Setup logging."""
    from logging.handlers import RotatingFileHandler
    from logging import Formatter
    log_file_path = app.config.get('LOG_FILE')
    log_level = app.config.get('LOG_LEVEL', logging.WARN)
    if log_file_path:  # pragma: no cover
        file_handler = RotatingFileHandler(log_file_path)
        file_handler.setFormatter(Formatter(
            '%(name)s:%(levelname)s:[%(asctime)s] %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        logger = logging.getLogger('pybossa')
        logger.setLevel(log_level)
        logger.addHandler(file_handler)


def setup_login_manager(app):
    """Setup login manager."""
    login_manager.login_view = 'account.signin'
    login_manager.login_message = "Please sign in to access this page."

    @login_manager.user_loader
    def _load_user(username):
        return user_repo.get_by_name(username)
    login_manager.setup_app(app)


def setup_babel(app):
    """Return babel handler."""
    babel.init_app(app)

    @babel.localeselector
    def _get_locale():
        from flask import request
        locales = [l[0] for l in app.config.get('LOCALES')]
        if current_user.is_authenticated:
           lang = current_user.locale
        else:
            lang = request.cookies.get('language')
        if (lang is None or lang == '' or
                lang.lower() not in locales):
            lang = request.accept_languages.best_match(locales)
        if (lang is None or lang == '' or
                lang.lower() not in locales):
            lang = app.config.get('DEFAULT_LOCALE') or 'en'
        if request.headers.get('Content-Type') == 'application/json':
            lang = 'en'
        return lang.lower()
    return babel


def setup_blueprints(app):
    """Configure blueprints."""
    from pybossa.api import blueprint as api
    from pybossa.view.account import blueprint as account
    from pybossa.view.projects import blueprint as projects
    from pybossa.view.admin import blueprint as admin
    from pybossa.view.announcements import blueprint as announcements
    from pybossa.view.leaderboard import blueprint as leaderboard
    from pybossa.view.stats import blueprint as stats
    from pybossa.view.help import blueprint as helper
    from pybossa.view.home import blueprint as home
    from pybossa.view.uploads import blueprint as uploads
    from pybossa.view.amazon import blueprint as amazon

    blueprints = [{'handler': home, 'url_prefix': '/'},
                  {'handler': api,  'url_prefix': '/api'},
                  {'handler': account, 'url_prefix': '/account'},
                  {'handler': projects, 'url_prefix': '/project'},
                  {'handler': admin, 'url_prefix': '/admin'},
                  {'handler': announcements, 'url_prefix': '/announcements'},
                  {'handler': leaderboard, 'url_prefix': '/leaderboard'},
                  {'handler': helper, 'url_prefix': '/help'},
                  {'handler': stats, 'url_prefix': '/stats'},
                  {'handler': uploads, 'url_prefix': '/uploads'},
                  {'handler': amazon, 'url_prefix': '/amazon'},
                  ]

    for bp in blueprints:
        app.register_blueprint(bp['handler'], url_prefix=bp['url_prefix'])

    # from rq_dashboard import RQDashboard
    import rq_dashboard
    app.config.from_object(rq_dashboard.default_settings)
    rq_dashboard.blueprint.before_request(is_admin)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/admin/rq",
                           redis_conn=sentinel.master)


def is_admin():
    """Check if user is admin."""
    if current_user.is_anonymous:
        return abort(401)
    if current_user.admin is False:
        return abort(403)


def setup_external_services(app):
    """Setup external services."""
    setup_twitter_login(app)
    setup_facebook_login(app)
    setup_google_login(app)
    setup_flickr_importer(app)
    setup_dropbox_importer(app)
    setup_twitter_importer(app)
    setup_youtube_importer(app)


def setup_twitter_login(app):
    try:  # pragma: no cover
        if (app.config['TWITTER_CONSUMER_KEY'] and
                app.config['TWITTER_CONSUMER_SECRET']):
            twitter.init_app(app)
            from pybossa.view.twitter import blueprint as twitter_bp
            app.register_blueprint(twitter_bp, url_prefix='/twitter')
    except Exception as inst:  # pragma: no cover
        print(type(inst))
        print(inst.args)
        print(inst)
        print("Twitter signin disabled")
        log_message = 'Twitter signin disabled: %s' % str(inst)
        app.logger.info(log_message)


def setup_facebook_login(app):
    try:  # pragma: no cover
        if (app.config['FACEBOOK_APP_ID']
                and app.config['FACEBOOK_APP_SECRET']
                and app.config.get('LDAP_HOST') is None):
            facebook.init_app(app)
            from pybossa.view.facebook import blueprint as facebook_bp
            app.register_blueprint(facebook_bp, url_prefix='/facebook')
    except Exception as inst:  # pragma: no cover
        print(type(inst))
        print(inst.args)
        print(inst)
        print("Facebook signin disabled")
        log_message = 'Facebook signin disabled: %s' % str(inst)
        app.logger.info(log_message)


def setup_google_login(app):
    try:  # pragma: no cover
        if (app.config['GOOGLE_CLIENT_ID']
                and app.config['GOOGLE_CLIENT_SECRET']
                and app.config.get('LDAP_HOST') is None):
            google.init_app(app)
            from pybossa.view.google import blueprint as google_bp
            app.register_blueprint(google_bp, url_prefix='/google')
    except Exception as inst:  # pragma: no cover
        print(type(inst))
        print(inst.args)
        print(inst)
        print("Google signin disabled")
        log_message = 'Google signin disabled: %s' % str(inst)
        app.logger.info(log_message)


def setup_flickr_importer(app):
    try:  # pragma: no cover
        if (app.config['FLICKR_API_KEY']
                and app.config['FLICKR_SHARED_SECRET']):
            flickr.init_app(app)
            from pybossa.view.flickr import blueprint as flickr_bp
            app.register_blueprint(flickr_bp, url_prefix='/flickr')
            importer_params = {'api_key': app.config['FLICKR_API_KEY']}
            importer.register_flickr_importer(importer_params)
    except Exception as inst:  # pragma: no cover
        print(type(inst))
        print(inst.args)
        print(inst)
        print("Flickr importer not available")
        log_message = 'Flickr importer not available: %s' % str(inst)
        app.logger.info(log_message)


def setup_dropbox_importer(app):
    try:  # pragma: no cover
        if app.config['DROPBOX_APP_KEY']:
            importer.register_dropbox_importer()
    except Exception as inst:  # pragma: no cover
        print(type(inst))
        print(inst.args)
        print(inst)
        print("Dropbox importer not available")
        log_message = 'Dropbox importer not available: %s' % str(inst)
        app.logger.info(log_message)


def setup_twitter_importer(app):
    try:  # pragma: no cover
        if (app.config['TWITTER_CONSUMER_KEY'] and
                app.config['TWITTER_CONSUMER_SECRET']):
            importer_params = {
                'consumer_key': app.config['TWITTER_CONSUMER_KEY'],
                'consumer_secret': app.config['TWITTER_CONSUMER_SECRET']
            }
            importer.register_twitter_importer(importer_params)
    except Exception as inst:  # pragma: no cover
        print(type(inst))
        print(inst.args)
        print(inst)
        print("Twitter importer not available")
        log_message = 'Twitter importer not available: %s' % str(inst)
        app.logger.info(log_message)


def setup_youtube_importer(app):
    try:  # pragma: no cover
        if app.config['YOUTUBE_API_SERVER_KEY']:
            importer_params = {
                'youtube_api_server_key': app.config['YOUTUBE_API_SERVER_KEY']
            }
            importer.register_youtube_importer(importer_params)
    except Exception as inst:  # pragma: no cover
        print(type(inst))
        print(inst.args)
        print(inst)
        print("Youtube importer not available")
        log_message = 'Youtube importer not available: %s' % str(inst)
        app.logger.info(log_message)


def url_for_other_page(page):
    """Setup url for other pages."""
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def setup_jinja(app):
    """Setup jinja."""
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page


def setup_error_handlers(app):
    """Setup error handlers."""

    from flask_wtf.csrf import CSRFError
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        response = dict(template='400.html', code=400,
                        description=CSRFERROR)
        return handle_content_type(response)

    @app.errorhandler(400)
    def _bad_request(e):
        response = dict(template='400.html', code=400,
                        description=BADREQUEST)
        return handle_content_type(response)

    @app.errorhandler(404)
    def _page_not_found(e):
        response = dict(template='404.html', code=404,
                        description=NOTFOUND)
        return handle_content_type(response)

    @app.errorhandler(500)
    def _server_error(e):  # pragma: no cover
        response = dict(template='500.html', code=500,
                        description=INTERNALSERVERERROR)
        return handle_content_type(response)

    @app.errorhandler(403)
    def _forbidden(e):
        response = dict(template='403.html', code=403,
                        description=FORBIDDEN)
        return handle_content_type(response)

    @app.errorhandler(401)
    def _unauthorized(e):
        response = dict(template='401.html', code=401,
                        description=UNAUTHORIZED)
        return handle_content_type(response)


def setup_hooks(app):
    """Setup hooks."""
    @app.after_request
    def _inject_x_rate_headers(response):
        limit = get_view_rate_limit()
        if limit and limit.send_x_headers:
            h = response.headers
            h.add('X-RateLimit-Remaining', str(limit.remaining))
            h.add('X-RateLimit-Limit', str(limit.limit))
            h.add('X-RateLimit-Reset', str(limit.reset))
        return response

    @app.before_request
    def _api_authentication():
        """ Attempt API authentication on a per-request basis."""
        apikey = request.args.get('api_key', None)
        from flask import _request_ctx_stack
        if 'Authorization' in request.headers:
            apikey = request.headers.get('Authorization')
        if apikey:
            user = user_repo.get_by(api_key=apikey)
            if user:
                _request_ctx_stack.top.user = user
        # Handle forms
        request.body = request.form
        if (request.method == 'POST' and
                request.headers.get('Content-Type') == 'application/json' and
                request.data):
            try:
                request.body = get_json_multidict(request)
            except TypeError:
                abort(400)

    @app.context_processor
    def _global_template_context():
        notify_admin = False
        if (current_user and current_user.is_authenticated
            and current_user.admin):
            key = NEWS_FEED_KEY + str(current_user.id)
            if sentinel.slave.get(key):
                notify_admin = True
            news = get_news()
        else:
            news = None

        # Cookies warning
        cookie_name = app.config['BRAND'] + "_accept_cookies"
        show_cookies_warning = False
        if request and (not request.cookies.get(cookie_name)):
            show_cookies_warning = True

        # Announcement sections
        if app.config.get('ANNOUNCEMENT'):
            announcement = app.config['ANNOUNCEMENT']
            if current_user and current_user.is_authenticated:
                for key in list(announcement.keys()):
                    if key == 'admin' and current_user.admin:
                        flash(announcement[key], 'info')
                    if key == 'owner' and len(current_user.projects) != 0:
                        flash(announcement[key], 'info')
                    if key == 'user':
                        flash(announcement[key], 'info')

        if app.config.get('CONTACT_EMAIL'):  # pragma: no cover
            contact_email = app.config.get('CONTACT_EMAIL')
        else:
            contact_email = 'info@pybossa.com'

        if app.config.get('CONTACT_TWITTER'):  # pragma: no cover
            contact_twitter = app.config.get('CONTACT_TWITTER')
        else:
            contact_twitter = 'PYBOSSA'

        # Available plugins
        plugins = plugin_manager.plugins

        # LDAP enabled
        ldap_enabled = app.config.get('LDAP_HOST', False)

        return dict(
            brand=app.config['BRAND'],
            title=app.config['TITLE'],
            logo=app.config['LOGO'],
            copyright=app.config['COPYRIGHT'],
            description=app.config['DESCRIPTION'],
            terms_of_use=app.config['TERMSOFUSE'],
            data_use=app.config['DATAUSE'],
            enforce_privacy=app.config['ENFORCE_PRIVACY'],
            # version=pybossa.__version__,
            current_user=current_user,
            show_cookies_warning=show_cookies_warning,
            contact_email=contact_email,
            contact_twitter=contact_twitter,
            upload_method=app.config['UPLOAD_METHOD'],
            news=news,
            notify_admin=notify_admin,
            plugins=plugins,
            ldap_enabled=ldap_enabled)

    @csrf.error_handler
    def csrf_error_handler(reason):
        response = dict(template='400.html', code=400,
                        description=reason)
        return handle_content_type(response)


def setup_jinja2_filters(app):
    """Setup jinja2 filters."""
    @app.template_filter('pretty_date')
    def _pretty_date_filter(s):
        return pretty_date(s)

    @app.template_filter('humanize_intword')
    def _humanize_intword(obj):
        return humanize.intword(obj)

    @app.template_filter('disqus_sso')
    def _disqus_sso(obj):  # pragma: no cover
        return get_disqus_sso(obj)


def setup_csrf_protection(app):
    """Setup csrf protection."""
    csrf.init_app(app)


def setup_debug_toolbar(app):  # pragma: no cover
    """Setup debug toolbar."""
    if app.config['ENABLE_DEBUG_TOOLBAR']:
        debug_toolbar.init_app(app)


def setup_ratelimits(app):
    """Setup ratelimits."""
    global ratelimits
    ratelimits['LIMIT'] = app.config['LIMIT']
    ratelimits['PER'] = app.config['PER']


def setup_cache_timeouts(app):
    """Setup cache timeouts."""
    global timeouts
    # Apps
    timeouts['AVATAR_TIMEOUT'] = app.config['AVATAR_TIMEOUT']
    timeouts['APP_TIMEOUT'] = app.config['APP_TIMEOUT']
    timeouts['REGISTERED_USERS_TIMEOUT'] = \
        app.config['REGISTERED_USERS_TIMEOUT']
    timeouts['ANON_USERS_TIMEOUT'] = app.config['ANON_USERS_TIMEOUT']
    timeouts['STATS_FRONTPAGE_TIMEOUT'] = app.config['STATS_FRONTPAGE_TIMEOUT']
    timeouts['STATS_APP_TIMEOUT'] = app.config['STATS_APP_TIMEOUT']
    timeouts['STATS_DRAFT_TIMEOUT'] = app.config['STATS_DRAFT_TIMEOUT']
    timeouts['N_APPS_PER_CATEGORY_TIMEOUT'] = \
        app.config['N_APPS_PER_CATEGORY_TIMEOUT']
    # Categories
    timeouts['CATEGORY_TIMEOUT'] = app.config['CATEGORY_TIMEOUT']
    # Users
    timeouts['USER_TIMEOUT'] = app.config['USER_TIMEOUT']
    timeouts['USER_TOP_TIMEOUT'] = app.config['USER_TOP_TIMEOUT']
    timeouts['USER_TOTAL_TIMEOUT'] = app.config['USER_TOTAL_TIMEOUT']


def setup_scheduled_jobs(app):  # pragma: no cover
    """Setup scheduled jobs."""
    from datetime import datetime
    from pybossa.jobs import enqueue_periodic_jobs, schedule_job, \
        get_quarterly_date
    from rq_scheduler import Scheduler
    redis_conn = sentinel.master
    scheduler = Scheduler(queue_name='scheduled_jobs', connection=redis_conn)
    MINUTE = 60
    HOUR = 60 * 60
    MONTH = 30 * (24 * HOUR)
    first_quaterly_execution = get_quarterly_date(datetime.utcnow())
    JOBS = [dict(name=enqueue_periodic_jobs, args=['email'], kwargs={},
                 interval=(1 * MINUTE), timeout=(10 * MINUTE)),
            dict(name=enqueue_periodic_jobs, args=['maintenance'], kwargs={},
                 interval=(1 * MINUTE), timeout=(10 * MINUTE)),
            dict(name=enqueue_periodic_jobs, args=['super'], kwargs={},
                 interval=(10 * MINUTE), timeout=(10 * MINUTE)),
            dict(name=enqueue_periodic_jobs, args=['high'], kwargs={},
                 interval=(1 * HOUR), timeout=(10 * MINUTE)),
            dict(name=enqueue_periodic_jobs, args=['medium'], kwargs={},
                 interval=(12 * HOUR), timeout=(10 * MINUTE)),
            dict(name=enqueue_periodic_jobs, args=['low'], kwargs={},
                 interval=(24 * HOUR), timeout=(10 * MINUTE)),
            dict(name=enqueue_periodic_jobs, args=['monthly'], kwargs={},
                 interval=(1 * MONTH), timeout=(30 * MINUTE)),
            dict(name=enqueue_periodic_jobs, args=['bimonthly'], kwargs={},
                 interval=(2 * MONTH), timeout=(2 * HOUR)),
            dict(name=enqueue_periodic_jobs, args=['quaterly'], kwargs={},
                 interval=(3 * MONTH), timeout=(30 * MINUTE),
                 scheduled_time=first_quaterly_execution)]

    for job in JOBS:
        schedule_job(job, scheduler)


def setup_newsletter(app):
    """Setup mailchimp newsletter."""
    if app.config.get('MAILCHIMP_API_KEY'):
        newsletter.init_app(app)


def setup_assets(app):
    """Setup assets."""
    from flask_assets import Environment
    assets = Environment(app)


def setup_strong_password(app):
    global enable_strong_password
    enable_strong_password = app.config.get('ENABLE_STRONG_PASSWORD')


def setup_ldap(app):
    if app.config.get('LDAP_HOST'):
        ldap.init_app(app)


def setup_profiler(app):
    if app.config.get('FLASK_PROFILER'):
        flask_profiler.init_app(app)


def setup_upref_mdata(app):
    """Setup user preference and metadata choices for user accounts"""
    global upref_mdata_choices
    upref_mdata_choices = dict(languages=[], locations=[],
                               timezones=[], user_types=[])
    if app.config.upref_mdata:
        from settings_upref_mdata import (upref_languages, upref_locations,
                                          mdata_timezones, mdata_user_types)
        upref_mdata_choices['languages'] = upref_languages()
        upref_mdata_choices['locations'] = upref_locations()
        upref_mdata_choices['timezones'] = mdata_timezones()
        upref_mdata_choices['user_types'] = mdata_user_types()
