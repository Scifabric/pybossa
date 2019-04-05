from setuptools import setup, find_packages

requirements = [
    "alembic>=0.6.4, <1.0",
    "beautifulsoup4>=4.3.2, <5.0",
    "blinker>=1.3, <2.0",
    "Flask-Babel>=0.9, <0.10",
    "Flask-Login >=0.3.0, <0.4",                      # was pinned to Flask-Login==0.2.3 in the past. GitHub version 3.0+ is used now.
    "Flask-Mail>=0.9.0, <1.0",
    "misaka>=1.0.0, <2.0.0",
    "Flask-Misaka>=0.2.0, <0.4.0",
    "Flask-OAuthlib>=0.9.5, <0.9.6",
    # "Flask-SQLAlchemy>=2.0, <2.1",
    # "Flask-OAuthlib>=0.9.1, <0.9.2",
    "oauthlib>=2.1.0,<2.1.1",
    "Flask-SQLAlchemy>=2.3, <2.4",
    "Flask-WTF>=0.9.5, <0.9.6",         # was pinned to Flask-WTF==0.9.5
    "Flask>=1.0.2, <1.0.3",           # was pinned to Flask==0.10.1
    "html2text>=2014.4.5, <2014.9.7",
    "itsdangerous>=0.24, <1.0",
    "rsa>=3.4.2",
    "markdown>=2.4, <3.0",
    "psycopg2-binary>=2.7.5, <3.0",
    "python-dateutil>=2.2, <3.0",
    "raven>=6.9.0, <7.0.0",
    "pyOpenSSL>=16.2",                  # fix for python below 2.7.9
    "ndg-httpsclient>=0.4.0, <1.0",     # fix for python below 2.7.9
    "pyasn1>=0.1.7, <1.0",              # fix for python below 2.7.9
    "requests>=2.2.1, <3.0",
    "SQLAlchemy>=1.1.7, <1.1.8",
    "six>=1.9.0, <2.0.0",
    "nose",
    "rednose",
    "redis==3.0.1",
    "coverage",
    "nose-cov",
    "mock",
    "pyrax>=1.9.6, <2.0",
    "pillow>=3.3.2, <3.3.3",
    "flask-debugtoolbar>=0.9.0, <1.0",
    "factory_boy>=2.4.1, <2.5",
    "rq==0.13",
    "rq-scheduler==0.9",
    "rq-dashboard==0.3.12",
    "unidecode>=0.04.16, <0.05",
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
    "flatten-json==0.1.6",
    "boto>=2.48.0, <2.49",
    "python-magic>=0.4.13, <0.4.14",
    "wtforms-components>=0.10.3, <0.10.4",
    "otpauth>=1.0.1, <1.0.2",
    "Flask-SimpleLDAP >=1.1.2, <1.1.3",
    "flask_profiler >= 1.6, <1.6.1",
    "wtforms-components>=0.10.3, <0.10.4",
    "yacryptopan",
    "Faker",
    "flask-talisman>=0.5.0, <0.6.0",
    "cryptography>=2.3.1, <2.4.0",
    "python-saml>=2.4.0, <2.5.0",
    "hdfs[kerberos]>=2.2.1, <2.3.0",
    "iiif-prezi>=0.2.9, <1.0.0",
    "Werkzeug>=0.14.0, <0.15.0"
]

setup(
    name = 'pybossa',
    version = '2.11.0',
    packages = find_packages(),
    install_requires = requirements,
    # only needed when installing directly from setup.py (PyPi, eggs?) and pointing to e.g. a git repo.
    # Keep in mind that dependency_links are not used when installing with requirements.txt
    # and need to be added redundant to requirements.txt in this case!
    # Example:
    # dependency_links = ['git+https://github.com/Hypernode/M2Crypto#egg=M2Crypto-0.22.dev'],

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
