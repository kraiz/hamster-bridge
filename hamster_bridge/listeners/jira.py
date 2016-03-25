from __future__ import absolute_import

from jira import JIRA, JIRAError

from hamster_bridge.listeners import (
    HamsterListener,
    ConfigValue,
)

import logging
import re
from getpass import getpass

logger = logging.getLogger(__name__)


class JiraHamsterListener(HamsterListener):

    short_name = 'jira'

    config_values = [
        ConfigValue(
            key='server_url',
            setup_func=lambda: raw_input('Root url to your jira server [f.e. "http://jira.example.org"]\n'),
            sensitive=False,
        ),
        ConfigValue(
            key='username',
            setup_func=lambda: raw_input('Your jira user name\n'),
            sensitive=False,
        ),
        ConfigValue(
            key='password',
            setup_func=lambda: getpass('Your jira password\n'),
            sensitive=True,
        ),
        ConfigValue(
            key='auto_start',
            setup_func=lambda: raw_input('Automatically start the issue when you start the task in hamster? [y/n]\n'),
            sensitive=False,
        ),
    ]

    issue_from_title = re.compile('([A-Z][A-Z0-9]+-[0-9]+)')

    # noinspection PyBroadException
    def prepare(self):
        server_url = self.get_from_config('server_url')
        username = self.get_from_config('username')
        password = self.get_from_config('password')

        logger.info('Connecting as "%s" to "%s"', username, server_url)
        self.jira = JIRA(server_url, basic_auth=(username, password))

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
        if auto_start == 'y':
            try:
                issue_name = self.__issue_from_fact(fact)
                if issue_name is None:
                    return

                for transition in self.jira.transitions(issue_name):
                    if transition['name'] == u'Start Progress':
                        self.jira.transition_issue(issue_name, transition['id'])
                        logger.info('Marked issue "%s" as "In Progress"', issue_name)
            except JIRAError:
                logger.exception('Error communicating with Jira')

    def on_fact_stopped(self, fact):
        time_spent = '%dm' % (fact.delta.total_seconds() / 60)
        issue_name = self.__issue_from_fact(fact)
        if issue_name:
            try:
                worklog = self.jira.add_worklog(issue_name, time_spent, comment=fact.description)
                logger.info('Logged work: %s to %s (created %r)', time_spent, issue_name, worklog)
            except JIRAError:
                logger.exception('Error communicating with Jira')
        else:
            logger.debug('No jira issue found')
