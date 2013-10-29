from setuptools import setup
execfile('morbo/version.py')

setup(
    name = 'morbo',
    version = __version__,
    packages = ['morbo'],
    description = 'A MongoDB object mapper for puny humans.',
    author = 'Elisha Cook',
    author_email = 'elisha@elishacook.com',
    url = 'https://github.com/elishacook/morbo',
    download_url = 'https://github.com/elishacook/morbo/tarball/1.0.0',
    test_suite = 'tests',
    install_requires=[
        'pymongo>=2.6.2'
    ],
    setup_requires=['nose>=1.0']
)
