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
    test_suite = 'tests',
    install_requires=[
        'pymongo'
    ],
    setup_requires=['nose']
)
