# -*- coding: utf-8 -*-

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

long_description = """
============
Secretary
============
Take the power of Jinja2 templates to OpenOffice or LibreOffice and create reports and letters in your web applications.

See full `documentation on Github <https://github.com/christopher-ramirez/secretary/blob/master/README.md>`_
."""

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='secretary',
    version='0.3.4',
    url='https://github.com/bijanebrahimi/secretary',
    license='MIT',
    author='Bijan Ebrahimi',
    author_email='bijanebrahimi@riseup.net',
    description='Take the power of Jinja2 templates to OpenOffice or LibreOffice.',
    long_description=long_description,
    packages=['secretary'],
    platforms='any',
    install_requires=[
        'Jinja2', 'markdown2', 'ordereddict'
    ],
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    test_suite='test_secretary',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Office/Business',
        'Topic :: Utilities',
    ],
    extras_require={
        'testing': ['pytest']
    }
)
