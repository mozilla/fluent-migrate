#!/usr/bin/env python

from setuptools import setup

setup(name='fluent.migrate',
      version='0.6.4',
      description='Toolchain to migrate legacy translation to Fluent.',
      author='Mozilla',
      author_email='l10n-drivers@mozilla.org',
      license='APL 2',
      url='https://hg.mozilla.org/l10n/fluent-migration/',
      keywords=['fluent', 'localization', 'l10n'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 2.7',
      ],
      packages=['fluent.migrate'],
      install_requires=[
          'compare-locales >=3.0, <4.0'
      ],
      test_suite='tests.migrate'
)
