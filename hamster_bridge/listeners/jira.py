from __future__ import absolute_import
import os
# MAX patch
import sys

from jira import JIRA, JIRAError

from hamster_bridge.listeners import (
    HamsterListener,
    ConfigValue,
)

import logging
import re
import datetime
from dateutil.tz import *
from getpass import getpass

logger = logging.getLogger(__name__)


class JiraHamsterListener(HamsterListener):

    short_name = 'jira'

    config_values = [
        ConfigValue(
            key='server_url',
            setup_func=lambda: raw_input('Root url of your jira server [f.e. "http://jira.example.org"]: '),
            sensitive=False,
        ),
        ConfigValue(
            key='username',
            setup_func=lambda: raw_input('Your jira user name: '),
            sensitive=False,
        ),
        ConfigValue(
            key='password',
            setup_func=lambda: getpass('Your jira password: ') if sys.stdin.isatty() else raw_input(),
            sensitive=True,
        ),
        ConfigValue(
            key='auto_start',
            setup_func=lambda: raw_input('Automatically start the issue when '
                'you start the task in hamster?  You can also specify the name of '
                'the JIRA transition to use.  [y/n/TRANSITION_NAME]: '),
            sensitive=False,
        ),
        ConfigValue(
            key='verify_ssl',
            setup_func=lambda: raw_input('Verify HTTPS/SSL connections?  '
                'You can also specify the path to a CA certificate bundle.  [y/n/PATH]: '),
            sensitive=False,
        ),
    ]

    issue_from_title = re.compile('([A-Z][A-Z0-9]+-[0-9]+)')

    # noinspection PyBroadException
    def prepare(self):
        server_url = self.get_from_config('server_url')
        username = self.get_from_config('username')
        password = self.get_from_config('password')
        verify_ssl = self.get_from_config('verify_ssl')

        options = {}
        if verify_ssl.lower() in ('y', 'true'):
            logger.info("Enabling SSL/TLS certificate verification (default CA path)")
            options['verify'] = True
        elif verify_ssl.lower() in ('n', 'false'):
            logger.warn("Disabling SSL/TLS certificate verification")
            options['verify'] = False
        elif os.path.isfile(verify_ssl):
            logger.info("Enabling SSL/TLS certificate verification (custom CA "
                "path) '%s'", verify_ssl)
            options['verify'] = verify_ssl
        else:
            logger.error("verify_ssl = '%s' is not a valid CA cert path nor a "
                "valid option. Falling back to enabling SSL/TLS verification "
                "with default CA path", verify_ssl)
            options['verify'] = True

        logger.info('Connecting as "%s" to "%s"', username, server_url)
        self.jira = JIRA(
            server_url,
            options=options,
            basic_auth=(username, password)
        )

        try:
            self.jira.projects()
        except:
            logger.exception('Can not connect to JIRA, please check ~/.hamster-bridge.cfg')

    def __issue_from_fact(self, fact):
        """
        Get the issue name from a fact
        :param fact: the fact to search the issue in
        """
        fields = [fact.activity] + fact.tags
        logger.debug('Searching ticket in: %r', fields)
        for field in fields:
            for possible_issue in self.issue_from_title.findall(field):
                logger.debug('Lookup issue for activity "%s"', possible_issue)
                try:
                    self.jira.issue(possible_issue)
                    logger.debug('Found existing issue "%s" in "%s"', possible_issue, field)
                    return possible_issue
                except JIRAError, e:
                    if e.text == 'Issue Does Not Exist':
                        logger.warning('Tried issue "%s", but does not exist. ', possible_issue)
                    else:
                        logger.exception('Error communicating with Jira')

    def on_fact_started(self, fact):
        auto_start = self.get_from_config('auto_start')
        if auto_start.lower() in ('n', 'false'):
            return
        elif auto_start.lower() in ('y', 'true'):
            transition_name = u'Start Progress'
        else:
            transition_name = unicode(auto_start, 'utf-8')
        try:
            issue_name = self.__issue_from_fact(fact)
            if issue_name is None:
                return

            transition_found = False
            transitions = self.jira.transitions(issue_name)
            for transition in transitions:
                if transition['name'] == transition_name:
                    transition_found = True
                    self.jira.transition_issue(issue_name, transition['id'])
                    logger.info('Marked issue "%s" as "%s"', issue_name, transition_name)
            if not transition_found:
                logger.warn(
                    "Could not find transition '%s' in '%s'",
                    transition_name,
                    [t['name'] for t in transitions]
                )
        except JIRAError:
            logger.exception('Error communicating with Jira')

    def on_fact_stopped(self, fact):
        time_spent = '%dm' % (fact.delta.total_seconds() / 60)
        issue_name = self.__issue_from_fact(fact)
        tstart = fact.start_time
        if issue_name:
            try:
                logger.info('Log work: %s - %s to %s', tstart, time_spent, issue_name)
                if tstart.tzinfo is None:
                    logger.info("Start time without timezone. Use local timzone info!")
                    tstart = tstart.replace(tzinfo=tzlocal())
                worklog = self.jira.add_worklog(issue_name, time_spent, started=tstart, comment=fact.description)
                logger.info('Logged work: %s - %s to %s (created %r)', fact.start_time, time_spent, issue_name, worklog)
            except JIRAError:
                logger.exception('Error communicating with Jira')
        else:
            logger.debug('No jira issue found')
