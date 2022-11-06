import os
from setuptools import setup, find_packages
HERE = os.path.abspath(os.path.dirname(__file__))
PKG_NAME='TrainerEngine'
VERPATH = os.path.join(HERE, PKG_NAME, '_version.py')
exec(open(VERPATH).read())

setup(name=PKG_NAME,
      version=__version__,
      author="Mikolaj Krawczuk",
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
      'pysimplegui'
      ],
      entry_points='''
      [console_scripts]
      sofia=TrainerEngine.main:init
    ''')
