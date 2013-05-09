import json
import logging
from operator import pos
import re
import requests

from hamster_bridge.listeners import HamsterListener


logger = logging.getLogger(__name__)


# TODO method documentation
class RedmineHamsterListener(HamsterListener):
    """
    Redmine listener for hamster tasks,
    """

    short_name = 'redmine'

    # TODO initial setup does not complete after entering API key :-(
    config_values = [
        ('server_url', lambda: raw_input('Root URL to the Redmine server [f.e. "http://redmine.example.org"]\n')),
        ('api_key', lambda: raw_input('Your Redmine API access key.\n')),
    ]

    resources = {
        'issue': 'issues/%(issue)s.json',
        'time_entries': 'time_entries.json',
    }

    issue_from_title = re.compile('([0-9]+)\ ')

    def __request_resource(self, resource, method='get', data=None):
        kwargs = {
            'headers': {
                'X-Redmine-API-Key': self.config.get(self.short_name, 'api_key'),
                'content-type': 'application/json',
            }
        }

        if data is not None and method == 'put':
            kwargs['data'] = data

        return getattr(requests, method)(
            '%(url)s%(resource)s' % {
                'url': self.config.get(self.short_name, 'server_url'),
                'resource': resource,
            },
            **kwargs
        )

    def __get_time_entry_json(self, issue_id, date, time_spent):
        return json.dumps(
            {
                'time_entry': {
                    'issue_id': issue_id,
                    'spent_on': date,
                    'hours': time_spent,
                }
            }
        )

    def __log_work(self, issue, time_spent):
        # TODO implement
        logger.info('Logged work: %s to %s', time_spent, issue)

    def __get_issue_from_fact(self, fact):
        # iterate the possible issues, normally this should match exactly one...
        for possible_issue in self.issue_from_title.findall(fact.activity):
            # check if there is an issue with this id in Redmine
            req = self.__request_resource(self.resources['issue'] % {'issue': possible_issue})
            if req.status_code == 200:
                del req
                return possible_issue

        return None

    def prepare(self):
        # check connectivity and API key validity,
        req = self.__request_resource(self.resources['time_entries'])
        if req.status_code != 200:
            logger.exception('Could not connect to Redmine and call the REST API, please check ~/.hamster-bridge.cfg')

    def on_fact_started(self, fact):
        # TODO implement
        pass

    def on_fact_stopped(self, fact):
        issue = self.__get_issue_from_fact(fact)
        if issue is not None:
            self.__log_work(issue, '%0.2f' % (fact.delta.total_seconds() / 3600.0))
        else:
            logger.info('No valid issue found in "%s"', fact.activity)