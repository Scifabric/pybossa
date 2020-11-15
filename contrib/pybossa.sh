[ ! -d "/home/vagrant/.pyenv" ] && curl https://pyenv.run | bash

export PATH="/home/vagrant/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

tee -a ~/home/vagrant/.bashrc << END

export PATH="/home/vagrant/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

END

pyenv install 3.6.12
pyenv global 3.6.12
echo setting up PYBOSSA...
git clone --recursive https://github.com/Scifabric/pybossa
cd pybossa
python -mvenv env
source env/bin/activate
pip install -U pip
pip install -r requirements.txt
cp settings_local.py.tmpl settings_local.py
cp alembic.ini.template alembic.ini
redis-server contrib/sentinel.conf --sentinel
python cli.py db_create
python run.py
