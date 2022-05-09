try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


config = {
    'description': 'Create number of road miles at census block level using faces and edges tiger file using 50/50 method and independent method',
    'author': 'Murtaza Nasafi',
    'author_email': 'murtaza.nasafi@fcc.gov',
    'version': 1.0,
    'install_requires': ['nose', 'arcpy', 'pandas'],
    'packages': [],
    'scripts': [],
    'name': "Road Maker"
}
setup(**config)
