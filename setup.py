#!/usr/bin/env python
from setuptools import setup


setup(
    name='hamster-bridge',
    description='let your hamster log your work to your favorite bugtracker',
    version='0.7.0',
    author='Lars Kreisz',
    author_email='lars.kreisz@gmail.com',
    license='MIT',
    url='https://github.com/kraiz/hamster-bridge',
    extras_require={
        'redmine': ['python-redmine'],
    },
    packages=['hamster_bridge', 'hamster_bridge.listeners'],
    entry_points={'console_scripts': ['hamster-bridge = hamster_bridge:main']},
    long_description=open('README.rst').read(),
    install_requires=['jira>=0.41']
)
