# -*- coding: utf-8 -*-
import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now
#   1) we have a top level README file and
#   2) it's easier to type in the README file than to put a raw string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='secretary',
    version='0.0.1',
    url='https://github.com/christopher-ramirez/secretary',
    license='BSD',
    author='Christopher Ramírez',
    author_email='chris.ramirezg@gmail.com',
    description=('Take the power of Jinja2 templates to OpenOffice and '
                 'LibreOffice and create reports and letters in your web applications'),
    long_description=read('README.md'),
    py_modules=['secretary'],
    platforms='any',
    install_requires=[
        'Jinja2',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Office/Business',
        'Topic :: Utilities',
    ]
)
