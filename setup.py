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


__version__ = '?'
with open('./version', 'r') as f:
    __version__ = f.read()

setup(
    name='Secretary',
    version=__version__,
    url='https://github.com/christopher-ramirez/secretary',
    license='MIT',
    author='Christopher Ramírez',
    author_email='chris.ramirezg@gmail.com',
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
    keywords='Document engine Libreoffice OpenOffice Jinja Jinja2',
    description='Take the power of Jinja2 templates to OpenOffice or LibreOffice.',
    install_requires=['jinja2', 'markdown2'],
    python_requires='>=2.6',
    long_description=long_description,
    packages=['secretary'],
    platforms='any',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    test_suite='test_secretary',
    extras_require={
        'testing': ['pytest']
    }
)
