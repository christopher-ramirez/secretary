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
    version='0.2.15',
    url='https://github.com/christopher-ramirez/secretary',
    license='MIT',
    author='Christopher Ramírez',
    author_email='chris.ramirezg@gmail.com',
    description='Take the power of Jinja2 templates to OpenOffice or LibreOffice.',
    long_description=long_description,
    py_modules=['secretary', 'markdown_map'],
    platforms='any',
    install_requires=[
        'Jinja2', 'markdown2'
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
