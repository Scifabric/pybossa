package 'postgresql-9.1'
package "postgresql-server-dev-9.1" 

apt_package "python-dev" do
    action :install
end

apt_package "python-virtualenv" do
    action :install
end

apt_package "swig" do
    action :install
end


execute "Create virtualenv" do
    command "virtualenv vagrant_env"
    cwd "/opt/"
end


execute "install pybossa requirements" do
    command ". /opt/vagrant_env/bin/activate; pip install -e ."
    cwd "/vagrant"
end

execute "install pybossa cache requirements" do
    command ". /opt/vagrant_env/bin/activate; pip install -r cache_requirements.txt"
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

execute "create user db pybossa" do
    command <<-EOH
    psql -c "CREATE USER pybossa WITH CREATEDB LOGIN PASSWORD 'tester'"
    EOH
    user "postgres"
end

execute "create pybossa DB" do
    command "createdb pybossa -O pybossa --encoding='utf-8' --locale=en_US.utf8 --template=template0"
    user "postgres"
end

execute "populate pybossa db" do
    command ". /opt/vagrant_env/bin/activate; python cli.py db_create"
    cwd "/vagrant"
end
