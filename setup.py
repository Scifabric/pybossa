from setuptools import setup, find_packages
try:
    requirements = open('requirements.txt').read().split('\n')
except:
    requirements = []

setup(
    name = 'pybossa',
    version = '0.2.1',
    packages = find_packages(),
    install_requires = requirements,
    dependency_links = ['git+https://github.com/Hypernode/M2Crypto#egg=M2Crypto-0.22.dev'],
    # metadata for upload to PyPI
    author = 'Sf Isle of Man Limited',
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

