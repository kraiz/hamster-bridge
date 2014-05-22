#!/usr/bin/env python
from setuptools import setup


setup(
    name='hamster-bridge',
    description='let your hamster log your work to your favorite bugtracker',
    version='0.4.0',
    author='Lars Kreisz',
    author_email='der.kraiz@gmail.com',
    license='MIT',
    url='https://github.com/kraiz/hamster-bridge',
    packages=['hamster_bridge', 'hamster_bridge.listeners'],
    entry_points={'console_scripts': ['hamster-bridge = hamster_bridge:main']},
    long_description=open('README.rst').read(),
    install_requires = [
        'oauthlib>0.3.7',
        'jira-python>=0.13'
    ]
)