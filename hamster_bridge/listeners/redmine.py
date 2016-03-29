from __future__ import absolute_import
import os

import logging
import re

from hamster_bridge.listeners import (
    HamsterListener,
    ConfigValue,
)


logger = logging.getLogger(__name__)


class RedmineHamsterListener(HamsterListener):
    """
    Redmine listener for hamster tasks,
    Tested with Redmine 2.5.1.stable

    Important: will only work with German or English installation!

    INFO: Unfortunately the Redmine API returns issue statuses in the currently set language.
          There is only the id and the name of the status.
          f.e. "New" has usually ID 1, but its name would be "Neu" in a German installation.
    """
    short_name = 'redmine'

    config_values = [
        ConfigValue(
            key='server_url',
            setup_func=lambda: raw_input('Root URL to the Redmine server [f.e. "http://redmine.example.org/"]\n'),
            sensitive=False,
        ),
        ConfigValue(
            key='api_key',
            setup_func=lambda: raw_input('Your Redmine API access key.\n'),
            sensitive=False,
        ),
        ConfigValue(
            key='version',
            setup_func=lambda: raw_input('The Redmine version number, e.g. 2.5.1\n'),
            sensitive=False,
        ),
        ConfigValue(
            key='auto_start',
            setup_func=lambda: raw_input('Automatically start the issue when you start the task in hamster? [y/n]\n'),
            sensitive=False,
        ),
        ConfigValue(
            key='verify_ssl',
            setup_func=lambda: raw_input('Verify HTTPS/SSL connections? '
                'You can also specify the path to a CA certificate bundle. [y/n/PATH]\n'),
            sensitive=False,
        ),
    ]

    # Redmine issue key is just a number
    issue_from_title = re.compile('([0-9]+)\ ')

    def __init__(self):
        """
        Sets up the class be defining some internal variables.
        """
        # issue status dict for the default issue status
        self.__issue_status_default = None

        # issue status dict for the "in Work" status
        self.__issue_status_in_work = None

        # the redmine instance
        self.redmine = None

        # will store the activities
        self.__activities = {}

    def __get_issue_from_fact(self, fact):
        """
        Tries to find an issue matching the given fact.

        :param fact: the currently stopped fact
        :type fact: hamster.lib.stuff.Fact
        :returns: the issue or None if not found
        :rtype:
        """
        from redmine.exceptions import ResourceNotFoundError
        
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

    def __get_first_activity_id(self):
        """
        Returns the first activity that was retrieved.
        The first activity was marked with a True value.
        :return: the id of the first activity
        :rtype: int
        """
        return [key for key, value in self.__activities.items() if value[1]][0]

    def __get_activity_id(self, tags):
        """
        Returns an activity id if it can be resolved from the list of given tags.
        Otherwise the first found activity id is returned.
        :param tags: list of tags
        :type tags: list
        :return: the activity id
        :rtype: int
        """
        if len(tags) == 0:
            # this grabs the first activity from the dict
            return self.__get_first_activity_id()
        else:
            for activity_id, activity_value in self.__activities.viewitems():
                try:
                    next(tag for tag in tags if tag == activity_value[0])
                    return activity_id
                except StopIteration:
                    # if not found
                    continue

            # fallback if no tag matches
            return self.__get_first_activity_id()

    def prepare(self):
        """
        Prepares the listener by checking connectivity to configured Redmine instance.
        While doing so, grabs the issue statuses, too, used for on_fact_stopped.
        """
        from redmine import Redmine
        from redmine.exceptions import BaseRedmineError
        
        verify_ssl = self.get_from_config('verify_ssl')
        requests_dict = {}
        if verify_ssl.lower() in ('y', 'true'):
            logger.info("Enabling SSL/TLS certificate verification (default CA path)")
            requests_dict['verify'] = True
        elif verify_ssl.lower() in ('n', 'false'):
            logger.warn("Disabling SSL/TLS certificate verification")
            requests_dict['verify'] = False
        elif os.path.isfile(verify_ssl):
            logger.info("Enabling SSL/TLS certificate verification (custom CA "
                "path) '%s'", verify_ssl)
            requests_dict['verify'] = verify_ssl
        else:
            logger.error("verify_ssl = '%s' is not a valid CA cert path nor a "
                "valid option. Falling back to enabling SSL/TLS verification "
                "with default CA path", verify_ssl)
            requests_dict['verify'] = True

        # setup the redmine instance
        self.redmine = Redmine(
            self.get_from_config('server_url'),
            key=self.get_from_config('api_key'),
            version=self.get_from_config('version'),
            requests=requests_dict,
        )
        # fetch the possible activities for time entries
        time_entry_activities = self.redmine.enumeration.filter(resource='time_entry_activities')

        # only now the real http request is made, use this as connectivity check
        try:
            logger.info('### Available Redmine activities for using as tag value:')
            is_first = True
            for tea in time_entry_activities:
                self.__activities[tea.id] = (tea.name, is_first)
                is_first = False
                logger.info('### ' + tea.name)
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
        auto_start = self.get_from_config('auto_start')
        if auto_start == 'y':
            # fetch the issue from the hamster fact
            issue = self.__get_issue_from_fact(fact)

            # abort if no issue was found
            if not issue:
                logger.error('Unable to query issue for starting of hamster fact %s', fact.original_activity)
                return

            # if the issue is in the default state (aka the initial state), put it into work state
            if issue.status.id == self.__issue_status_default.id:
                logger.info('setting status to "In Work" for issue %d', issue.id)
                issue.status_id = self.__issue_status_in_work.id
                issue.save()

    def on_fact_stopped(self, fact):
        """
        Called by HamsterBridge if a fact is stopped.
        Will try to log the time to the appropriate Redmine issue if there is one.
        Uses the first found issue.

        :param fact: the currently stopped fact
        :type fact: hamster.lib.stuff.Fact
        """

        # fetch the issue from the hamster fact
        issue = self.__get_issue_from_fact(fact)

        # abort if no issue was found
        if not issue:
            logger.error('Unable to query issue for stopping of hamster fact %s', fact.original_activity)
            return

        # create the time entry
        self.redmine.time_entry.create(
            issue_id=issue.id,
            hours='%0.2f' % (fact.delta.total_seconds() / 3600.0),
            # grep the tags, convert to string (the values are dbus.String) and find an activity
            activity_id=self.__get_activity_id([str(tag) for tag in fact.tags]),
            comments=fact.description,
        )
