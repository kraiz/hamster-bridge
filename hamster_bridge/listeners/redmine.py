from __future__ import absolute_import

import json
import logging
import re
import requests

from hamster_bridge.listeners import HamsterListener

from redmine import Redmine
from redmine.exceptions import (
    BaseRedmineError,
    ResourceNotFoundError,
)


logger = logging.getLogger(__name__)


class RedmineHamsterListener(HamsterListener):
    """
    Redmine listener for hamster tasks,
    Tested with Redmine 2.2.2.stable

    Important: will only work with German or English installation!

    INFO: Unfortunately the Redmine API returns issue statuses in the currently set language.
          There is only the id and the name of the status.
          f.e. "New" has usually ID 1, but its name would be "Neu" in a German installation.
    """
    short_name = 'redmine'

    config_values = [
        ('server_url', lambda: raw_input('Root URL to the Redmine server [f.e. "http://redmine.example.org/"]\n')),
        ('api_key', lambda: raw_input('Your Redmine API access key.\n')),
        ('version', lambda: raw_input('The Redmine version number, e.g. 2.5.1\n')),
        ('auto_start', lambda: raw_input('Automatically start the issue when you start the task in hamster? [y/n]\n')),
        # FIXME still usable?
        ('verify_ssl', lambda: raw_input('Verify HTTPS/SSL connections? [y/n]\n')),
    ]

    # Redmine issue key is just a number
    issue_from_title = re.compile('([0-9]+)\ ')

    def __get_config(self, key):
        """
        Returns the config value with the given key.
        :param key: the key to get
        :type key: basestring
        :return: the config value
        :rtype: basestring
        """
        return self.config.get(self.short_name, key)

    def __init__(self):
        """
        Sets up the class be defining some internal variables.
        """
        # FIXME still necessary?
        # will store the issue statuses as returned by Redmine API during the call of RedmineHamsterListener.prepare
        self.__issues_statuses = []
        # FIXME still necessary?
        # will store the issue data, will be updated per issue whenever an issue is requested on the API
        self.__issues = {}
        # FIXME still necessary?
        # issue status dict for the default issue status
        self.__issue_status_default = None
        # FIXME still necessary?
        # issue status dict for the "in Work" status
        self.__issue_status_in_work = None

        # the redmine instance
        self.redmine = None

        # will store the activities
        self.__activities = {}

        # will store the currently active issue
        self.issue = None

    # FIXME still necessary?
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
            },
            'verify': True if self.config.get(self.short_name, 'verify_ssl') == 'y' else False,
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

    # FIXME still necessary?
    def __update_issue(self, issue_id, data):
        """
        Updates the issue with the given id with the given data.

        :param issue_id: the id of the issue
        :type issue_id: str
        :param data: the data to update
        :type data: dict
        """
        req = self.__request_resource(
            self.resources['issue'] % {'issue_id': issue_id},
            method='put',
            data=json.dumps(data),
        )
        if req.status_code != 200:
            logger.error('Unable to set issue %(issue_id)s to data %(data)s.' % {'issue_id': issue_id, 'data': data})

    # FIXME still necessary?
    def __log_work(self, issue_number, date_spent_on, time_spent):
        """
        Logs work to Redmine with the given values.

        :param issue_number: the issue to log to
        :type issue_number: str
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
            logger.error('Unable to log time to Redmine. HTTP status code was %s with error %s', req.status_code, req.text)

    # FIXME still necessary?
    def __exists_issue(self, issue_id):
        """
        Checks if an issue with the given issue_id exists by calling the Redmine API,

        :param issue_id: the issue id
        :type issue_id: str
        """
        req = self.__request_resource(self.resources['issue'] % {'issue_id': issue_id})
        if req.status_code == 200:
            # cache the issue values for later use
            self.__issues[issue_id] = req.json()['issue']
            return True

        return False

    def __get_issue_from_fact(self, fact):
        """
        Tries to find an issue matching the given fact.

        :param fact: the currently stopped fact
        :type fact: hamster.lib.stuff.Fact
        :returns: the issue or None if not found
        :rtype:
        """
        # iterate the possible issues, normally this should match exactly one...
        for possible_issue in self.issue_from_title.findall(fact.activity):
            try:
                return self.redmine.issue.get(possible_issue)
            except ResourceNotFoundError:
                return None

        return None

    def __filter_issue_statuses(self):
        """
        Filters the issue statuses for the relevant ones: the default and the status "In Work".
        """

        def find_default(element):
            """
            Filter function to find the default issue status.
            """
            return hasattr(element, 'is_default') and getattr(element, 'is_default', False)

        def find_in_work(element):
            """
            Filter function to find the in work status.
            """
            return element.name in [u'In Bearbeitung', u'In Work']

        # get the issue statuses
        issue_statuses = self.redmine.issue_status.all()

        # if none are found, raise
        if len(issue_statuses) == 0:
            logger.exception('Unable to fetch issue statuses! Not possible to proceed!')

        try:
            self.__issue_status_default = [item for item in issue_statuses if find_default(item)][0]
        except IndexError:
            logger.exception('Unable to find a single default issue status!')

        try:
            self.__issue_status_in_work = [item for item in issue_statuses if find_in_work(item)][0]
        except IndexError:
            logger.exception('Unable to find a single "In Work" issue status!')

    def prepare(self):
        """
        Prepares the listener by checking connectivity to configured Redmine instance.
        While doing so, grabs the issue statuses, too, used for on_fact_stopped.
        """
        # setup the redmine instance
        self.redmine = Redmine(
            self.__get_config('server_url'),
            key=self.__get_config('api_key'),
            version=self.__get_config('version'),
            requests={
                'verify': True if self.__get_config('verify_ssl') == 'y' else False
            }
        )
        # fetch the possible activities for time entries
        time_entry_activities = self.redmine.enumeration.filter(resource='time_entry_activities')

        # only now the real http request is made, use this as connectivity check
        try:
            for tea in time_entry_activities:
                self.__activities[tea.id] = tea.name
        except (BaseRedmineError, IOError):
            logger.exception('Unable to communicate with redmine server. See error in the following output:')

        # fetch all available issue statuses and filter the default and in work ones as they are the only relevant statuses here
        self.__filter_issue_statuses()

    def on_fact_started(self, fact):
        """
        Called by HamsterBridge if a fact is started.
        Will try to start the appropriate Redmine issue if there is one.
        Uses the first found issue.

        :param fact: the currently stopped fact
        :type fact: hamster.lib.stuff.Fact
        """
        # if issue shall be auto started...
        if self.config.get(self.short_name, 'auto_start') == 'y':
            # fetch the issue from the hamster fact
            self.issue = self.__get_issue_from_fact(fact)

            if not self.issue:
                logger.error('Unable to query an issue for the hamster fact %s', fact.original_activity)
                return

            # if the issue is in the default state (aka the initial state), put it into work state
            if self.issue.status.id == self.__issue_status_default.id:
                logger.info('setting status to "In Work" for issue %d', self.issue.id)
                self.issue.status_id = self.__issue_status_in_work.id
                self.issue.save()

    # FIXME still necessary?
    def on_fact_stopped(self, fact):
        # FIXME remove
        print('on_fact_stopped', fact)
        # TODO handle self.issue
        """
        Called by HamsterBridge if a fact is stopped.
        Will try to log the time to the appropriate Redmine issue if there is one.
        Uses the first found issue.

        :param fact: the currently stopped fact
        :type fact: hamster.lib.stuff.Fact
        """
        issue_id = self.__get_issue_id_from_fact(fact)
        if issue_id is not None:
            self.__log_work(issue_id, fact.date, '%0.2f' % (fact.delta.total_seconds() / 3600.0))
        else:
            logger.info('No valid issue found in "%s"', fact.activity)
