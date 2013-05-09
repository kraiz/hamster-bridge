import json
import logging
import re
import requests

from hamster_bridge.listeners import HamsterListener


logger = logging.getLogger(__name__)


class RedmineHamsterListener(HamsterListener):
    """
    Redmine listener for hamster tasks,
    """

    short_name = 'redmine'

    # TODO initial setup does not complete after entering API key :-(
    config_values = [
        ('server_url', lambda: raw_input('Root URL to the Redmine server [f.e. "http://redmine.example.org/"]\n')),
        ('api_key', lambda: raw_input('Your Redmine API access key.\n')),
    ]

    # Redmine API resources
    resources = {
        'issue': 'issues/%(issue)s.json',
        'time_entries': 'time_entries.json',
    }

    # Redmine issue key is just a number
    issue_from_title = re.compile('([0-9]+)\ ')

    def __request_resource(self, resource, method='get', data=None):
        """
        Request the given resource from the Redmine API using the given method.
        If method is PUT or POST, also sent the given data.

        :param resource: the URL to call on Redmine API
        :type resource: str
        :param method: the HTTP method
        :type method: str
        :param data: the data to put if method is PUT or POST
        :type data: str
        """
        kwargs = {
            'headers': {
                'X-Redmine-API-Key': self.config.get(self.short_name, 'api_key'),
                'content-type': 'application/json',
            }
        }

        if data is not None and (method == 'put' or method == 'post'):
            kwargs['data'] = data

        url = self.config.get(self.short_name, 'server_url')
        if not url.endswith('/'):
            url += '/'

        return getattr(requests, method)(
            '%(url)s%(resource)s' % {
                'url': url,
                'resource': resource,
            },
            **kwargs
        )

    def __log_work(self, issue_number, date_spent_on, time_spent):
        """
        Logs work to Redmine with the given values.

        :param issue_number: the issue to log to
        :type issue_number: unicode
        :param date_spent_on: the date the time was spent
        :type date_spent_on: datetime.date
        :param time_spent: the amount of time that was spent
        :type time_spent: str
        """
        req = self.__request_resource(
            self.resources['time_entries'],
            method='post',
            data=json.dumps(
                {
                    'time_entry': {
                        'issue_id': issue_number,
                        'spent_on': date_spent_on.strftime('%Y-%m-%d'),
                        'hours': time_spent,
                    }
                }
            )
        )
        if req.status_code == 201:
            logger.info('Logged work: %(time_spent)s to %(issue)s on %(date_spent_on)s' % {
                'time_spent': time_spent,
                'issue': issue_number,
                'date_spent_on': date_spent_on,
            })
        else:
            logger.error('Unable to log time to Redmine. HTTP status code was %s' % req.status_code)

    def __get_issue_from_fact(self, fact):
        """
        Tries to find an issue matching the given fact.

        :param fact: the currently stopped fact
        :type fact: hamster.lib.stuff.Fact
        :returns: the issue (number) or None if not found
        :rtype: str
        """
        # iterate the possible issues, normally this should match exactly one...
        for possible_issue in self.issue_from_title.findall(fact.activity):
            # check if there is an issue with this id in Redmine
            req = self.__request_resource(self.resources['issue'] % {'issue': possible_issue})
            if req.status_code == 200:
                del req
                return possible_issue

        return None

    def prepare(self):
        """
        Prepares the listener by checking connectivity to configured Redmine instance.
        """
        # check connectivity and API key validity,
        req = self.__request_resource(self.resources['time_entries'])
        if req.status_code != 200:
            logger.error('Could not connect to Redmine and call the REST API, please check ~/.hamster-bridge.cfg')

    def on_fact_started(self, fact):
        # TODO implement
        pass

    def on_fact_stopped(self, fact):
        """
        Called by HamsterBridge if a fact is stopped.

        :param fact: the currently stopped fact
        :type fact: hamster.lib.stuff.Fact
        """
        issue = self.__get_issue_from_fact(fact)
        if issue is not None:
            self.__log_work(issue, fact.date, '%0.2f' % (fact.delta.total_seconds() / 3600.0))
        else:
            logger.info('No valid issue found in "%s"', fact.activity)
