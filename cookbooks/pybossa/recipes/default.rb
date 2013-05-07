package "postgresql-server-dev-9.1" 
package "python-dev"

user "pybossa" do
  home "/home/pybossa"
  shell "/bin/bash"
end

directory "/home/pybossa" do
  owner "pybossa"
  group "pybossa"
  mode 0755
  action :create
end

git "Clone" do
    repository "git://github.com/PyBossa/pybossa.git"
    reference "master"
    action :checkout
    destination "/home/pybossa/pybossa/"
    user "pybossa"
    group "pybossa"
    enable_submodules true
end

python_virtualenv "/home/pybossa/pybossa/env" do
    owner "pybossa"
    group "pybossa"
    action :create
end

execute "install pybossa requirements" do
    command ". env/bin/activate; pip install -e /home/pybossa/pybossa"
    cwd "/home/pybossa/pybossa"
    user "pybossa"
end

execute "setup pybossa DB" do
    command "cp alembic.ini.template alembic.ini"
    user "pybossa"
    cwd "/home/pybossa/pybossa"
end

execute "setup pybossa DB" do
    command "cp settings_local.py.tmpl settings_local.py"
    user "pybossa"
    cwd "/home/pybossa/pybossa"
end

execute "create user db tester" do
    command <<-EOH
    psql -c "CREATE USER tester WITH CREATEDB LOGIN PASSWORD 'tester'"
    EOH
    user "postgres"
end

execute "create pybossa DB" do
    command "createdb pybossa -O tester"
    user "postgres"
end

execute "populate pybossa db" do
    command ". env/bin/activate; python cli.py db_create"
    user "pybossa"
    cwd "/home/pybossa/pybossa"
end
