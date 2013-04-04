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

from StringIO import StringIO
from flask import Blueprint, request, url_for, flash, redirect, abort, Response, current_app
from flask import render_template, make_response
from flaskext.wtf import Form, IntegerField, TextField, BooleanField, \
    SelectField, validators, HiddenInput, TextAreaField
from flaskext.login import login_required, current_user
from flaskext.babel import lazy_gettext
from werkzeug.exceptions import HTTPException

import pybossa.model as model
import pybossa.stats as stats

from pybossa.core import db
from pybossa.model import App, Task
from pybossa.util import Unique, Pagination, UnicodeWriter
from pybossa.auth import require
from pybossa.cache import apps as cached_apps

import json
import importer
import presenter as presenter_module
import operator
import math

blueprint = Blueprint('app', __name__)


class AppForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      Unique(db.session, model.App, model.App.name,
                             message="Name is already taken.")])
    short_name = TextField(lazy_gettext('Short Name'),
                           [validators.Required(),
                            Unique(db.session, model.App, model.App.short_name,
                                   message=lazy_gettext("Short Name is already taken."))])
    description = TextField(lazy_gettext('Description'),
                            [validators.Required(
                                message=lazy_gettext("You must provide a description."))])
    thumbnail = TextField(lazy_gettext('Icon Link'))
    allow_anonymous_contributors = SelectField(lazy_gettext('Allow Anonymous Contributors'),
                                               choices=[('True', lazy_gettext('Yes')),
                                                        ('False', lazy_gettext('No'))])
    long_description = TextAreaField(lazy_gettext('Long Description'))
    sched = SelectField(lazy_gettext('Task Scheduler'),
                        choices=[('default', lazy_gettext('Default')),
                                 ('breadth_first', lazy_gettext('Breadth First')),
                                 ('depth_first', lazy_gettext('Depth First')),
                                 ('random', lazy_gettext('Random'))],)
    hidden = BooleanField(lazy_gettext('Hide?'))


class TaskPresenterForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    editor = TextAreaField('')


@blueprint.route('/', defaults={'page': 1})
@blueprint.route('/page/<int:page>')
def index(page):
    """By default show the Featured apps"""
    return app_index(page, cached_apps.get_featured, 'app-featured',
                     True, False)


def app_index(page, lookup, app_type, fallback, use_count):
    """Show apps of app_type"""
    if not require.app.read():
        abort(403)

    per_page = 5

    apps, count = lookup(page, per_page)

    if fallback and not apps:
        return redirect(url_for('.published'))

    pagination = Pagination(page, per_page, count)
    template_args = {
        "apps": apps,
        "title": lazy_gettext("Applications"),
        "pagination": pagination,
        "app_type": app_type}

    if use_count:
        template_args.update({"count": count})
    return render_template('/applications/index.html', **template_args)


@blueprint.route('/published', defaults={'page': 1})
@blueprint.route('/published/page/<int:page>')
def published(page):
    """Show the Published apps"""
    return app_index(page, cached_apps.get_published, 'app-published',
                     False, True)


@blueprint.route('/draft', defaults={'page': 1})
@blueprint.route('/draft/page/<int:page>')
def draft(page):
    """Show the Draft apps"""
    return app_index(page, cached_apps.get_draft, 'app-draft',
                     False, True)


@blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not require.app.create():
        abort(403)
    form = AppForm(request.form)

    def respond(errors):
        return render_template('applications/new.html',
                               title=lazy_gettext("Create an Application"),
                               form=form, errors=errors)

    if request.method != 'POST':
        return respond(False)

    if not form.validate():
        flash(lazy_gettext('Please correct the errors'), 'error')
        return respond(True)

    info = {}
    # Add the info items
    if form.thumbnail.data:
        info['thumbnail'] = form.thumbnail.data
    if form.sched.data:
        info['sched'] = form.sched.data

    app = model.App(name=form.name.data,
                    short_name=form.short_name.data,
                    description=form.description.data,
                    long_description=form.long_description.data,
                    hidden=int(form.hidden.data),
                    owner_id=current_user.id,
                    info=info,)

    cached_apps.reset()
    db.session.add(app)
    db.session.commit()
    # Clean cache
    msg_1 = lazy_gettext('Application created!')
    flash('<i class="icon-ok"></i> ' + msg_1, 'success')
    flash('<i class="icon-bullhorn"></i> ' +
          lazy_gettext('You can check the ') +
          '<strong><a href="https://docs.pybossa.com">' +
          lazy_gettext('Guide and Documentation') +
          '</a></strong> ' +
          lazy_gettext('for adding tasks, a thumbnail, using PyBossa.JS, etc.'),
          'info')
    return redirect(url_for('.settings', short_name=app.short_name))


@blueprint.route('/<short_name>/taskpresentereditor', methods=['GET', 'POST'])
@login_required
def task_presenter_editor(short_name):
    errors = False
    app = App.query.filter_by(short_name=short_name).first()

    if not app:
        abort(404)

    title = "Application: %s &middot; Task Presenter Editor" % app.name
    if not require.app.update(app):
        abort(403)

    form = TaskPresenterForm(request.form)
    if request.method == 'POST' and form.validate():
        app.info['task_presenter'] = form.editor.data
        db.session.add(app)
        db.session.commit()
        msg_1 = lazy_gettext('Task presenter added!')
        flash('<i class="icon-ok"></i> ' + msg_1, 'success')
        return redirect(url_for('.settings', short_name=app.short_name))

    if request.method == 'POST' and not form.validate():
        flash(lazy_gettext('Please correct the errors'), 'error')
        errors = True

    if request.method != 'GET':
        return

    if app.info.get('task_presenter'):
        form.editor.data = app.info['task_presenter']
    else:
        if not request.args.get('template'):
            msg_1 = lazy_gettext('<strong>Note</strong> You will need to upload the'
                                 ' tasks using the')
            msg_2 = lazy_gettext('CSV importer')
            msg_3 = lazy_gettext(' or download the app bundle and run the'
                                 ' <strong>createTasks.py</strong> script in your'
                                 ' computer')
            url = '<a href="%s"> %s</a>' % (url_for('app.import_task',
                                                    short_name=app.short_name), msg_2)
            msg = msg_1 + url + msg_3
            flash(msg, 'info')

            wrap = lambda i: "applications/presenters/%s.html" % i
            pres_tmpls = map(wrap, presenter_module.presenters)

            return render_template(
                'applications/task_presenter_options.html',
                title=title,
                app=app,
                presenters=pres_tmpls)

        tmpl_uri = "applications/snippets/%s.html" \
            % request.args.get('template')
        tmpl = render_template(tmpl_uri, app=app)
        form.editor.data = tmpl
        msg = 'Your code will be <em>automagically</em> rendered in \
                      the <strong>preview section</strong>. Click in the \
                      preview button!'
        flash(lazy_gettext(msg), 'info')
    return render_template('applications/task_presenter_editor.html',
                           title=title,
                           form=form,
                           app=app,
                           errors=errors)


@blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
@login_required
def delete(short_name):
    app = App.query.filter_by(short_name=short_name).first()
    if not app:
        abort(404)

    title = "Application: %s &middot; Delete" % app.name
    if not require.app.delete(app):
        abort(403)
    if request.method == 'GET':
        return render_template('/applications/delete.html',
                               title=title,
                               app=app)
    # Clean cache
    cached_apps.clean(app.id)
    db.session.delete(app)
    db.session.commit()
    flash(lazy_gettext('Application deleted!'), 'success')
    return redirect(url_for('account.profile'))


@blueprint.route('/<short_name>/update', methods=['GET', 'POST'])
@login_required
def update(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()

    def handle_valid_form(form):
        hidden = int(form.hidden.data)

        new_info = {}
        # Add the info items
        app = App.query.filter_by(short_name=short_name).first_or_404()
        if form.thumbnail.data:
            new_info['thumbnail'] = form.thumbnail.data
        if form.sched.data:
            new_info['sched'] = form.sched.data

        # Merge info object
        info = dict(app.info.items() + new_info.items())

        new_application = model.App(
            id=form.id.data,
            name=form.name.data,
            short_name=form.short_name.data,
            description=form.description.data,
            long_description=form.long_description.data,
            hidden=hidden,
            info=info,
            owner_id=app.owner_id,
            allow_anonymous_contributors=form.allow_anonymous_contributors.data)

        app = App.query.filter_by(short_name=short_name).first_or_404()
        db.session.merge(new_application)
        db.session.commit()
        flash(lazy_gettext('Application updated!'), 'success')
        return redirect(url_for('.details',
                                short_name=new_application.short_name))

    if not require.app.update(app):
        abort(403)

    title = "Application: %s &middot; Update" % app.name
    if request.method == 'GET':
        form = AppForm(obj=app)
        form.populate_obj(app)
        if app.info.get('thumbnail'):
            form.thumbnail.data = app.info['thumbnail']
        if app.info.get('sched'):
            for s in form.sched.choices:
                if app.info['sched'] == s[0]:
                    form.sched.data = s[0]
                    break

    if request.method == 'POST':
        form = AppForm(request.form)
        if form.validate():
            return handle_valid_form(form)
        flash(lazy_gettext('Please correct the errors'), 'error')

    return render_template('/applications/update.html',
                           form=form,
                           title=title,
                           app=app)


@blueprint.route('/<short_name>/')
def details(short_name):
    app = db.session.query(model.App)\
                    .filter(model.App.short_name == short_name)\
                    .first()
    if not app:
        abort(404)
    title = "Application: %s" % app.name

    template_args = {"app": app, "title": title}
    try:
        require.app.read(app)
        require.app.update(app)

        return render_template('/applications/actions.html', **template_args)
    except HTTPException:
        if app.hidden:
            template_args = {"app": None, "title": "Application not found"}
        return render_template('/applications/app.html', **template_args)


@blueprint.route('/<short_name>/settings')
@login_required
def settings(short_name):
    application = db.session.query(model.App)\
                    .filter(model.App.short_name == short_name)\
                    .first()

    if not application:
        abort(404)

    title = "Application: %s &middot; Settings" % application.name
    try:
        require.app.read(application)
        require.app.update(application)

        return render_template('/applications/settings.html',
                               app=application,
                               title=title)
    except HTTPException:
        return abort(403)

def compute_importer_variant_pairs(forms):
    """Return a list of pairs of importer variants. The pair-wise enumeration
    is due to UI design.
    """
    variants = reduce(operator.__add__,
                      [i.variants for i in forms.itervalues()],
                      [])
    if len(variants) % 2:
        variants.append("empty")

    prefix = "applications/tasks/"

    importer_variants = map(lambda i: "%s%s.html" % (prefix, i), variants)
    return [
        (importer_variants[i * 2], importer_variants[i * 2 + 1])
        for i in xrange(0, int(math.ceil(len(variants) / 2.0)))]

@blueprint.route('/<short_name>/import', methods=['GET', 'POST'])
def import_task(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    title = "Applications: %s &middot; Import Tasks" % app.name
    template_args = {"title": title, "app": app}

    data_handlers = dict([
        (i.template_id, (i.form_detector, i(request.form), i.form_id))
        for i in importer.importers])
    forms = [
        (i.form_id, i(request.form))
        for i in importer.importers]
    forms = dict(forms)
    template_args.update(forms)

    template_args["importer_variants"] = compute_importer_variant_pairs(forms)

    template = request.args.get('template')

    if not (template or request.method == 'POST'):
        return render_template('/applications/import_options.html',
                               **template_args)

    if template == 'gdocs':
        mode = request.args.get('mode')
        if mode is not None:
            template_args["gdform"].googledocs_url.data = importer.googledocs_urls[mode]

    # in future, we shall pass an identifier of the form/template used,
    # which we can receive here, and use for a dictionary lookup, rather than
    # this search mechanism
    form = None
    handler = None
    for k, v in data_handlers.iteritems():
        field_id, handler, form_name = v
        if field_id in request.form:
            form = template_args[form_name]
            template = k
            break

    def render_forms():
        tmpl = '/applications/importers/%s.html' % template
        return render_template(tmpl, **template_args)

    if not (form and form.validate_on_submit()):
        return render_forms()

    return _import_task(app, handler, form, render_forms)


def _import_task(app, handler, form, render_forms):
    try:
        empty = True
        for task_data in handler.tasks(form):
            task = model.Task(app=app)
            print task_data
            [setattr(task, k, v) for k, v in task_data.iteritems()]
            db.session.add(task)
            db.session.commit()
            empty = False
        if empty:
            raise importer.BulkImportException(lazy_gettext(
                    'Oops! It looks like the file is empty.'))
        flash(lazy_gettext('Tasks imported successfully!'), 'success')
        return redirect(url_for('.settings', short_name=app.short_name))
    except importer.BulkImportException, err_msg:
        flash(err_msg, 'error')
    except Exception as inst:
        print inst
        msg = 'Oops! Looks like there was an error with processing that file!'
        flash(lazy_gettext(msg), 'error')
    return render_forms()


@blueprint.route('/<short_name>/task/<int:task_id>')
def task_presenter(short_name, task_id):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    task = Task.query.filter_by(id=task_id).first_or_404()

    if current_user.is_anonymous():
        if not app.allow_anonymous_contributors:
            msg = ("Oops! You have to sign in to participate in "
                   "<strong>%s</strong>"
                   "application" % app.name)
            flash(lazy_gettext(msg), 'warning')
            return redirect(url_for('account.signin',
                                    next=url_for('.presenter',
                                                 short_name=app.short_name)))
        else:
            msg_1 = lazy_gettext(
                "Ooops! You are an anonymous user and will not "
                "get any credit"
                " for your contributions.")
            next_url = url_for(
                'app.task_presenter',
                short_name=short_name,
                task_id=task_id)
            url = url_for(
                'account.signin',
                next=next_url)
            flash(msg_1 + "<a href=\"" + url + "\">Sign in now!</a>", "warning")
    if app:
        title = "Application: %s &middot; Contribute" % app.name
    else:
        title = "Application not found"

    template_args = {"app": app, "title": title}

    def respond(tmpl):
        return render_template(tmpl, **template_args)

    if not (task.app_id == app.id):
        return respond('/applications/task/wrong.html')

    #return render_template('/applications/presenter.html', app = app)
    # Check if the user has submitted a task before

    tr_search = db.session.query(model.TaskRun)\
                  .filter(model.TaskRun.task_id == task_id)\
                  .filter(model.TaskRun.app_id == app.id)

    if current_user.is_anonymous():
        remote_addr = request.remote_addr or "127.0.0.1"
        tr = tr_search.filter(model.TaskRun.user_ip == remote_addr)
    else:
        tr = tr_search.filter(model.TaskRun.user_id == current_user.id)

    tr_first = tr.first()
    if tr_first is None:
        return respond('/applications/presenter.html')
    else:
        return respond('/applications/task/done.html')


@blueprint.route('/<short_name>/presenter')
@blueprint.route('/<short_name>/newtask')
def presenter(short_name):
    app = App.query.filter_by(short_name=short_name)\
        .first_or_404()
    title = "Application &middot; %s &middot; Contribute" % app.name
    template_args = {"app": app, "title": title}

    if not app.allow_anonymous_contributors and current_user.is_anonymous():
        msg = "Oops! You have to sign in to participate in <strong>%s</strong> \
               application" % app.name
        flash(lazy_gettext(msg), 'warning')
        return redirect(url_for('account.signin',
                        next=url_for('.presenter', short_name=app.short_name)))

    msg = "Ooops! You are an anonymous user and will not \
           get any credit for your contributions. Sign in \
           now!"

    def respond(tmpl):
        if (current_user.is_anonymous()):
            msg_1 = lazy_gettext(msg)
            flash(msg_1, "warning")
        resp = make_response(render_template(tmpl, **template_args))
        return resp

    if app.info.get("tutorial") and \
            request.cookies.get(app.short_name + "tutorial") is None:
        resp = respond('/applications/tutorial.html')
        resp.set_cookie(app.short_name + 'tutorial', 'seen')
        return resp
    else:
        return respond('/applications/presenter.html')


@blueprint.route('/<short_name>/tutorial')
def tutorial(short_name):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    if app:
        title = "Application: %s &middot; Tutorial" % app.name
    else:
        title = "Application not found"
    return render_template('/applications/tutorial.html', title=title, app=app)


@blueprint.route('/<short_name>/<int:task_id>/results.json')
def export(short_name, task_id):
    """Return a file with all the TaskRuns for a give Task"""
    app = db.session.query(model.App)\
            .filter(model.App.short_name == short_name)\
            .first()

    if not app:
        return abort(404)
    task = db.session.query(model.Task)\
        .filter(model.Task.id == task_id)\
        .first()

    results = [tr.dictize() for tr in task.task_runs]
    return Response(json.dumps(results), mimetype='application/json')


@blueprint.route('/<short_name>/tasks', defaults={'page': 1})
@blueprint.route('/<short_name>/tasks/<int:page>')
def tasks(short_name, page):
    app = App.query.filter_by(short_name=short_name).first_or_404()
    if app:
        title = "Application: %s &middot; Tasks" % app.name
    else:
        title = "Application not found"

    def respond():
        per_page = 10
        count = db.session.query(model.Task)\
            .filter_by(app_id=app.id)\
            .count()
        app_tasks = db.session.query(model.Task)\
            .filter_by(app_id=app.id)\
            .order_by(model.Task.id)\
            .limit(per_page)\
            .offset((page - 1) * per_page)\
            .all()

        if not app_tasks and page != 1:
            abort(404)

        pagination = Pagination(page, per_page, count)
        return render_template('/applications/tasks.html',
                               app=app,
                               tasks=app_tasks,
                               title=title,
                               pagination=pagination)

    try:
        require.app.read(app)
        require.app.update(app)
        return respond()
    except HTTPException:
        if not app.hidden:
            return respond()
        return render_template('/applications/tasks.html',
                               title="Application not found",
                               app=None)


@blueprint.route('/<short_name>/tasks/delete', methods=['GET', 'POST'])
@login_required
def delete_tasks(short_name):
    """Delete ALL the tasks for a given application"""
    app = App.query.filter_by(short_name=short_name).first_or_404()
    try:
        require.app.read(app)
        require.app.update(app)
        if request.method == 'GET':
            title = "Application Tasks: %s &middot; Delete" % app.name
            return render_template('applications/tasks/delete.html',
                                   app=app,
                                   title=title)
        else:
            for task in app.tasks:
                db.session.delete(task)
            db.session.commit()
            msg = "All the tasks and associated task runs have been deleted"
            flash(lazy_gettext(msg), 'success')
            return redirect(url_for('.settings', short_name=app.short_name))
    except HTTPException:
        return abort(403)


@blueprint.route('/<short_name>/export')
def export_to(short_name):
    """Export Tasks and TaskRuns in the given format"""
    app = App.query.filter_by(short_name=short_name).first_or_404()
    if app:
        title = "Application: %s &middot; Export" % app.name
    else:
        title = "Application not found"

    def gen_json(table):
        n = db.session.query(table)\
            .filter_by(app_id=app.id).count()
        sep = ", "
        yield "["
        for i, tr in enumerate(db.session.query(table)
                                 .filter_by(app_id=app.id).yield_per(1), 1):
            item = json.dumps(tr.dictize())
            if (i == n):
                sep = ""
            yield item + sep
        yield "]"

    def handle_task(writer, t):
        writer.writerow(t.info.values())

    def handle_task_run(writer, t):
        if (type(t.info) == dict):
            writer.writerow(t.info.values())
        else:
            writer.writerow([t.info])

    def get_csv(out, writer, table, handle_row):
        for tr in db.session.query(table)\
                .filter_by(app_id=app.id)\
                .yield_per(1):
            handle_row(writer, tr)
        yield out.getvalue()

    def respond_json(ty):
        tables = {"task": model.Task, "task_run": model.TaskRun}
        try:
            table = tables[ty]
        except KeyError:
            return abort(404)
        return Response(gen_json(table), mimetype='application/json')

    def respond_csv(ty):
        # Export Task(/Runs) to CSV
        types = {
            "task": (
                model.Task, handle_task,
                (lambda x: True),
                lazy_gettext(
                    "Oops, the application does not have tasks to \
                           export, if you are the owner add some tasks")),
            "task_run": (
                model.TaskRun, handle_task_run,
                (lambda x: type(x.info) == dict),
                lazy_gettext(
                    "Oops, there are no Task Runs yet to export, invite \
                           some users to participate"))}
        try:
            table, handle_row, test, msg = types[ty]
        except KeyError:
            return abort(404)

        out = StringIO()
        writer = UnicodeWriter(out)
        t = db.session.query(table)\
            .filter_by(app_id=app.id)\
            .first()
        if t is not None:
            if test(t):
                writer.writerow(t.info.keys())

            return Response(get_csv(out, writer, table, handle_row),
                            mimetype='text/csv')
        else:
            flash(msg, 'info')
            return render_template('/applications/export.html',
                                   title=title,
                                   app=app)

    ty = request.args.get('type')
    fmt = request.args.get('format')
    if not (fmt and ty):
        if len(request.args) >= 1:
            abort(404)
        return render_template('/applications/export.html',
                               title=title,
                               app=app)
    if fmt not in ["json", "csv"]:
        abort(404)
    return {"json": respond_json, "csv": respond_csv}[fmt](ty)


@blueprint.route('/<short_name>/stats')
def show_stats(short_name):
    """Returns App Stats"""
    app = db.session.query(model.App).filter_by(short_name=short_name).first()
    title = "Application: %s &middot; Statistics" % app.name

    if not (len(app.tasks) > 0 and len(app.task_runs) > 0):
        return render_template('/applications/non_stats.html',
                               title=title,
                               app=app)

    dates_stats, hours_stats, users_stats = stats.get_stats(
        app.id,
        current_app.config['GEO'])
    anon_pct_taskruns = int((users_stats['n_anon'] * 100) /
                            (users_stats['n_anon'] + users_stats['n_auth']))
    userStats = dict(
        geo=current_app.config['GEO'],
        anonymous=dict(
            users=users_stats['n_anon'],
            taskruns=users_stats['n_anon'],
            pct_taskruns=anon_pct_taskruns,
            top5=users_stats['anon']['top5']),
        authenticated=dict(
            users=users_stats['n_auth'],
            taskruns=users_stats['n_auth'],
            pct_taskruns=100 - anon_pct_taskruns,
            top5=users_stats['auth']['top5']))

    tmp = dict(userStats=users_stats['users'],
               userAnonStats=users_stats['anon'],
               userAuthStats=users_stats['auth'],
               dayStats=dates_stats,
               hourStats=hours_stats)

    return render_template('/applications/stats.html',
                           title=title,
                           appStats=json.dumps(tmp),
                           userStats=userStats,
                           app=app)
