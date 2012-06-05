from __future__ import with_statement
from fabric.api import *
from fabric.contrib.files import exists, append
from StringIO import StringIO

@task
def deploy(service_name, port=2090):
    '''Deploy (or upgrade) PyBossa service named `service_name` on optional
    `port` (default 2090)'''
    basedir = '/home/okfn/var/srvc' 
    app_dir = basedir + '/' + service_name
    src_dir = app_dir + '/' + 'src'
    code_dir = src_dir + '/' + 'pybossa'
    pip_path = app_dir + '/bin/pip'
    if not exists(src_dir):
        run('virtualenv %s' % app_dir)
        run('mkdir -p %s' % src_dir)
    run('%s install gunicorn' % pip_path)
    run('%s install -e git+https://github.com/PyBossa/pybossa#egg=pybossa' % pip_path)
    with cd(code_dir):
        run('git submodule init')
        run('git submodule update')

    supervisor_path = '/etc/supervisor/conf.d/%s.conf' % service_name
    if not exists(supervisor_path):
        log_path = app_dir + '/log'
        run('mkdir -p %s' % log_path)
        templated = supervisor_config % {
                'service_name': service_name,
                'app_dir': app_dir,
                'log_path': log_path,
                'port': port
                }
        put(StringIO(templated), supervisor_path, use_sudo=True) 
        sudo('/etc/init.d/supervisor status')
        sudo('/etc/init.d/supervisor force-reload')
    print('Restarting supervised process for %s' % service_name)
    sudo('supervisorctl restart %s' % service_name)
    print('You will now need to have your web server proxy to port: %s' % port)


supervisor_config = '''[program:%(service_name)s]
command=%(app_dir)s/bin/gunicorn "pybossa.web:app" --bind=127.0.0.1:%(port)s --workers=2 --max-requests=500 --name=%(service_name)s --error-logfile=%(log_path)s/%(service_name)s.gunicorn.error.log

; user that owns virtual environment.
user=okfn
 
stdout_logfile=%(log_path)s/%(service_name)s.log
stderr_logfile=%(log_path)s/%(service_name)s.error.log
autostart=true
'''

