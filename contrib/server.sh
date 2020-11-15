echo update package index files...
apt-get update -qq

echo installing required external libraries...
apt-get -y install git postgresql postgresql-server-dev-all libpq-dev python3-psycopg2 libsasl2-dev libldap2-dev libssl-dev python3-venv python-dev build-essential libjpeg-dev libssl-dev libffi-dev dbus libdbus-1-dev libdbus-glib-1-dev libldap2-dev libsasl2-dev redis-server python3-dev

sudo su postgres -c "psql -c \"CREATE ROLE pybossa SUPERUSER LOGIN PASSWORD 'tester'\" "
sudo su postgres -c "createdb pybossa -O pybossa"
