from setuptools import setup, find_packages

requirements = [
    "alembic>=0.6.4, <1.0",
    "beautifulsoup4>=4.3.2, <5.0",
    "blinker>=1.3, <2.0",
    "Flask-Babel>=0.9, <1.0",
    "Flask-Cache>=0.12, <1.0",
    "Flask-Gravatar>=0.4.1, <1.0",
    "flask-heroku>=0.1.8, <1.0",
    "Flask-Login",                      # was pinned to Flask-Login==0.2.3 in the past. GitHub version 3.0+ is used now.
    "Flask-Mail>=0.9.0, <1.0",
    "Flask-Misaka>=0.2.0, <1.0",
    "Flask-OAuth>=0.12, <0.13",         # was pinned to Flask-OAuth==0.12
    "Flask-SQLAlchemy>=2.0, <2.1",
    "Flask-WTF>=0.9.5, <0.9.6",         # was pinned to Flask-WTF==0.9.5
    "Flask>=0.10.1, <0.10.2",           # was pinned to Flask==0.10.1
    "html2text>=2014.4.5, <2014.9.7",
    "itsdangerous>=0.24, <1.0",
    "M2Crypto>=0.22.3, <0.22.4",        # let's be more restrictive on M2Crypto version
    "markdown>=2.4, <3.0",
    "psycopg2>=2.5.2, <3.0",
    "pygeoip>=0.3.1, <1.0",
    "python-dateutil>=2.2, <3.0",
    "raven>=4.1.1, <5.0",
    "requests>=2.2.1, <3.0",
    "SQLAlchemy>=0.9.6, <0.9.7",
    "six>=1.8.0, <1.9.0",
    "nose",
    "rednose",
    "redis>=2.9, <2.10",
    "sphinx>=1.2.2, <2.0",
    "coverage",
    "mock",
    "pyrax>=1.9.3, <2.0",
    "pillow>=2.4, <2.5",
    "flask-debugtoolbar>=0.9.0, <1.0",
    "factory_boy>=2.4.1, <2.5",
    "rq>=0.4.6, <0.5",
    "rq-scheduler",
    "rq-dashboard",
    "unidecode>=0.04.16, <0.05",
    "mailchimp"
]

setup(
    name = 'pybossa',
    version = '0.2.2',
    packages = find_packages(),
    install_requires = requirements,
    # only needed when installing directly from setup.py (PyPi, eggs?) and pointing to e.g. a git repo.
    # Keep in mind that dependency_links are not used when installing with requirements.txt
    # and need to be added redundant to requirements.txt in this case!
    # Example:
    # dependency_links = ['git+https://github.com/Hypernode/M2Crypto#egg=M2Crypto-0.22.dev'],
    dependency_links = ['git+https://github.com/maxcountryman/flask-login.git@13af160b3fd14dfb5f35f9cdc3863771efe194eb#egg=Flask-Login',
                        'git+https://github.com/PyBossa/rq-scheduler.git@2406f77fa08d465dd5b18801736538686dd24590#egg=rq-scheduler',
                        'git+https://github.com/PyBossa/rq-dashboard.git#egg=rq-dashboard'],

    # metadata for upload to PyPI
    author = 'SF Isle of Man Limited',
    # TODO: change
    author_email = 'info@pybossa.com',
    description = 'Open Source CrowdSourcing framework',
    long_description = '''PyBossa is an open source crowdsourcing solution for volunteer computing, thinking and sensing ''',
    license = 'AGPLv3',
    url = 'https://github.com/PyBossa/pybossa',
    download_url = '',
    include_package_data = True,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points = '''
    '''
)

