from setuptools import setup, find_packages
import sys, os

version = '0.5'

setup(name='rst2beamer',
      version=version,
      description="A docutils writer and script for converting restructured text to the Beamer presentation format",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='presentation docutils rst restructured-text',
      author='Ryan Krauss & Paul-Michael Agapow',
      author_email='agapow@bbsrc.ac.uk',
      url='http://www.agapow.net/software/rst2beamer',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
