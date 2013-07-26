package 'postgresql-9.1'
package "postgresql-server-dev-9.1" 
package "python-dev"

python_virtualenv "/opt/vagrant_env" do
    action :create
end

execute "install SWIG library" do
    command "apt-get install -y swig"
end

execute "install pybossa requirements" do
    command ". /opt/vagrant_env/bin/activate; pip install --pre -e ."
    cwd "/vagrant"
end

execute "setup pybossa DB" do
    command "cp alembic.ini.template alembic.ini"
    cwd "/vagrant"
end

execute "setup pybossa DB" do
    command "cp settings_local.py.tmpl settings_local.py"
    cwd "/vagrant"
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
    command ". /opt/vagrant_env/bin/activate; python cli.py db_create"
    cwd "/vagrant"
end
