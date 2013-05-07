from __future__ import absolute_import

from jira.exceptions import JIRAError
from jira.client import JIRA

from hamster_bridge.listeners import HamsterListener

import logging
import re

logger = logging.getLogger(__name__)


class JiraHamsterListener(HamsterListener):

    short_name = 'jira'

    config_values = [
        ('server_url', lambda: raw_input('Root url to your jira server [f.e. "http://jira.example.org"]\n')),
        ('username', lambda: raw_input('Your jira user name\n')),
        ('password', lambda: raw_input('Your jira password\n')),
        ('auto_start', lambda: raw_input('Automatically start the issue when you start the task in hamster? [y/n]\n'))
    ]

    issue_from_title = re.compile('([A-Z][A-Z0-9]+-[0-9]+)')

    # noinspection PyBroadException
    def prepare(self):
        self.jira = JIRA(
            options={'server': self.config.get(self.short_name, 'server_url')},
            basic_auth=(self.config.get(self.short_name, 'username'), self.config.get(self.short_name, 'password'))
        )
        # test
        try:
            self.jira.projects()
        except:
            logger.exception('Can not connect to JIRA, please check hamster-bridge.cfg')

    def __issue_from_fact(self, fact):
        """
        Get the issue name from a fact
        :param fact: the fact to search the issue in
        """
        for possible_issue in self.issue_from_title.findall(fact.activity):
            try:
                self.jira.issue(possible_issue)
                return possible_issue
            except JIRAError, e:
                if e.text == 'Issue Does Not Exist':
                    logger.warning('Tried Issue "%s", but does not exist. ', fact.activity)
                    continue
                else:
                    raise e
        return None

    def on_fact_started(self, fact):
        if self.config.get(self.short_name, 'auto_start') == 'y':
            try:
                issue_name = self.__issue_from_fact(fact)
                if issue_name is None:
                    return

                for transition in self.jira.transitions(issue_name):
                    if transition['name'] == u'Start Progress':
                        self.jira.transition_issue(issue_name, transition['id'])
                        logger.info('Marked issue "%s" as "In Progress"', issue_name)
            except JIRAError:
                logger.exception('Error communicating with Jira:')

    def on_fact_stopped(self, fact):
        time_spent = '%dm' % (fact.delta.total_seconds() / 60)

        try:
            issue_name = self.__issue_from_fact(fact)
            if issue_name is not None:
                self.jira.add_worklog(issue_name, time_spent)
                logger.info('Logged work: %s to %s', time_spent, issue_name)
            else:
                logger.info('No valid issue found in "%s"', fact.activity)

        except JIRAError:
            logger.exception('Error communicating with Jira:')