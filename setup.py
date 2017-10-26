from setuptools import setup, find_packages

requirements = [
    "alembic>=0.6.4, <1.0",
    "beautifulsoup4>=4.3.2, <5.0",
    "blinker>=1.3, <2.0",
    "Flask-Babel>=0.9, <0.10",
    "Flask-Login",                      # was pinned to Flask-Login==0.2.3 in the past. GitHub version 3.0+ is used now.
    "Flask-Mail>=0.9.0, <1.0",
    "misaka>=1.0.0, <2.0.0",
    "Flask-Misaka>=0.2.0, <0.4.0",
    "Flask-OAuthlib>=0.9.1, <0.9.2",
    "Flask-SQLAlchemy>=2.0, <2.1",
    "Flask-WTF>=0.9.5, <0.9.6",         # was pinned to Flask-WTF==0.9.5
    "Flask>=0.10.1, <0.10.2",           # was pinned to Flask==0.10.1
    "html2text>=2014.4.5, <2014.9.7",
    "itsdangerous>=0.24, <1.0",
    "rsa>=3.4.2",
    "markdown>=2.4, <3.0",
    "psycopg2>=2.5.2, <3.0",
    "pygeoip>=0.3.1, <1.0",
    "python-dateutil>=2.2, <3.0",
    "raven>=4.1.1, <5.0",
    "pyOpenSSL>=16.2",                  # fix for python below 2.7.9
    "ndg-httpsclient>=0.4.0, <1.0",     # fix for python below 2.7.9
    "pyasn1>=0.1.7, <1.0",              # fix for python below 2.7.9
    "requests>=2.2.1, <3.0",
    "SQLAlchemy>=1.1.7, <1.1.8",
    "six>=1.9.0, <2.0.0",
    "nose",
    "rednose",
    "redis>=2.9, <2.10",
    "coverage",
    "nose-cov",
    "mock",
    "pyrax>=1.9.6, <2.0",
    "pillow>=3.0, <3.1",
    "flask-debugtoolbar>=0.9.0, <1.0",
    "factory_boy>=2.4.1, <2.5",
    "rq>=0.4.6, <0.5",
    "rq-scheduler>=0.5.1, <0.5.2",
    "rq-dashboard",
    "unidecode>=0.04.16, <0.05",
    "mailchimp",
    "flask-plugins",
    "humanize",
    "pbr>=1.0, <2.0",                   # keep an eye on pbr: https://github.com/rackspace/pyrax/issues/561
    "feedparser",
    "twitter>=1.17.1, <1.18",
    "google-api-python-client>=1.5.0, <1.6.0",
    "Flask-Assets",
    "jsmin",
    "libsass",
    "pyjwt",
    "flask_json_multidict",
    "flask-cors>=3.0.2, <3.0.3",
    "webassets>=0.12.1, <0.12.2",
    "readability-lxml>=0.6.2, <1.0",
    "pybossa-onesignal",
    "pandas>=0.20.2, <0.20.3",
    "flatten-json",
    "otpauth>=1.0.1, <1.0.2",
    "Flask-SimpleLDAP >=1.1.2, <1.1.3",
]

setup(
    name = 'pybossa',
    version = '2.8.1',
    packages = find_packages(),
    install_requires = requirements,
    # only needed when installing directly from setup.py (PyPi, eggs?) and pointing to e.g. a git repo.
    # Keep in mind that dependency_links are not used when installing with requirements.txt
    # and need to be added redundant to requirements.txt in this case!
    # Example:
    # dependency_links = ['git+https://github.com/Hypernode/M2Crypto#egg=M2Crypto-0.22.dev'],
    dependency_links = ['git+https://github.com/maxcountryman/flask-login.git@13af160b3fd14dfb5f35f9cdc3863771efe194eb#egg=Flask-Login',
                        'git+https://github.com/Scifabric/rq-dashboard.git#egg=rq-dashboard',
                        'git+https://github.com/Scifabric/flatten.git@5d57cc6336df277822305ad70b86adf8c6a1c947#egg=flatten_json',
                        ],

    # metadata for upload to PyPI
    author = 'Scifabric LTD',
    author_email = 'info@scifabric.com',
    description = 'Open Source CrowdSourcing framework',
    long_description = '''PYBOSSA is the ultimate crowdsourcing framework to analyze or enrich data that can't be processed by machines alone.''',
    license = 'AGPLv3',
    url = 'http://pybossa.com',
    download_url = 'https://github.com/Scifabric/pybossa',
    include_package_data = True,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
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
