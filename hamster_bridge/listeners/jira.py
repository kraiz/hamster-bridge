from __future__ import absolute_import

from jira.exceptions import JIRAError
from jira.client import JIRA

from hamster_bridge.listeners import HamsterListener

import logging

logger = logging.getLogger(__name__)


class JiraHamsterListener(HamsterListener):

    short_name = 'jira'

    config_values = [
        ('server_url', 'the root url to your jira server [f.e. "http://jira.example.org"]'),
        ('username', 'your jira user name'),
        ('password', 'your jira password')
    ]

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

    def on_fact_stopped(self, fact):
        try:
            time_spent = '%dm' % (fact.delta.total_seconds() / 60)
            self.jira.add_worklog(fact.activity, time_spent)
            logger.info('Logged work: %s to %s', time_spent, fact.activity)
        except JIRAError, e:
            if e.text == 'Issue Does Not Exist':
                logger.warning('Issue "%s" does not exist. Ignoring...', fact.activity)
            else:
                logger.exception()