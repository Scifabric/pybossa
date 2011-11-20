from setuptools import setup, find_packages

setup(
    name = 'pybossa',
    version = '0.1a',
    packages = find_packages(),
    install_requires = [
        'Flask==0.8',
        'SQLAlchemy==0.7.3'
        ],
    # metadata for upload to PyPI
    author = 'Citizen Cyberscience Centre and Open Knowledge Foundation',
    # TODO: change
    author_email = 'info@okfn.org',
    description = 'pybossa is a RESTful data store for tabular and table-like data.',
    long_description = '''PyBossa is a rewrite of Bossa in Python.
    ''',
    license = 'MIT',
    url = 'https://github.com/citizen-cyberscience-centre/pybossa',
    download_url = '',
    include_package_data = True,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points = '''
    '''
)

