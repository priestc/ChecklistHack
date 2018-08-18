# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys

setup(
    name="ChecklistHack",
    version='0.1.0',
    description='Trading Card Checklist Utility',
    #long_description=open('README.md').read(),
    author='Chris Priest',
    author_email='cp368202@ohiou.edu',
    url='https://github.com/priestc/ChecklistHack',
    packages=find_packages(),
    scripts=['bin/clh'],
    include_package_data=True,
    license='LICENSE',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'requests',
        'tabulate',
        'beautifulsoup4',
        'natsort',
    ]
)
