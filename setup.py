try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


config = {
    'description': 'create number of road miles at census block level using faces and edges tiger file',
    'author': 'Murtaza Nasafi',
    'author_email': 'murtaza.nasafi@fcc.gov',
    'version': 0.1,
    'install_requires': ['nose', 'arcpy', 'pandas'],
    'packages': [],
    'scripts': [],
    'name': "Road Maker"
}
setup(**config)
