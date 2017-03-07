import ConfigParser
import datetime
import time
import logging
import os
import stat

logger = logging.getLogger(__name__)


try:
    import hamster.client
except ImportError:
    raise ImportError('Can not find hamster')


def _combine_configs(*configs):
    """
    Combines all configs (instances of RawConfigParser) into a single one
    containing all sections and values. If duplicates appear the later configs
    will overwrite the earlier values.
    Returns a RawConfigParser() instance.
    """
    result = ConfigParser.RawConfigParser()
    for config in configs:
        for section in config.sections():
            try:
                result.add_section(section)
            except ConfigParser.DuplicateSectionError:
                # Ignore it. We simply want to include all sections from
                # the source configs
                pass
            for option in config.options(section):
                value = config.get(section, option)
                result.set(section, option, value)
    return result


class HamsterBridge(hamster.client.Storage):
    """
    Connects to the running hamster instance via dbus. But as the notification does not work reliable there is a
    polling-based loop in the run()-method that will trigger all registered listeners.
    """
    def __init__(self, save_passwords=False):
        super(HamsterBridge, self).__init__()
        self._listeners = []
        self.save_passwords = save_passwords

    def add_listener(self, listener):
        """
        Registers the given HamsterListener instance. It will then be notified about changes.

        :param listener: the HamsterListener instance
        :type  listener: HamsterListener
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def configure(self, config_path):
        """
        Gives each listener the chance to do something before we start the bridge's runtime loops.
        :param config_path: path to config file
        :type config_path:  str
        """
        path = os.path.expanduser(config_path)
        config = ConfigParser.RawConfigParser()
        sensitive_config = ConfigParser.RawConfigParser()
        # read from file if exists
        if os.path.exists(path):
            logger.debug('Reading config file from %s', path)
            config.read(path)
        # let listeners extend
        for listener in self._listeners:
            logger.debug('Configuring listener %s', listener)
            listener.configure(config, sensitive_config)
        # save to file
        with open(path, 'wb') as configfile:
            logger.debug('Writing back configuration to %s', path)
            if self.save_passwords:
                all_configs = _combine_configs(config, sensitive_config)
                all_configs.write(configfile)
            else:
                config.write(configfile)
        # as we store passwords in clear text, let's at least set correct file permissions
        logger.debug('Setting owner only file permissions to %s', path)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

    def run(self, polling_intervall=1):
        """
        Starts the polling loop that will run until receive common exit signals.

        :param polling_intervall: how often the connector polls data from haster in seconds (default: 1)
        :type  polling_intervall: int
        """
        try:
            for listener in self._listeners:
                logger.debug('Preparing listener %s', listener)
                listener.prepare()
            logger.info('Start listening for hamster activity...')
            now = datetime.datetime.now().replace(microsecond=0)
            while True:
                last = now
                now = datetime.datetime.now().replace(microsecond=0)
                for fact in self.get_todays_facts():
                    if fact.start_time is not None and last <= fact.start_time < now:
                        logger.debug('Found a started task: %r', vars(fact))
                        for listener in self._listeners:
                            listener.on_fact_started(fact)
                    if fact.end_time is not None and last <= fact.end_time < now:
                        logger.debug('Found a stopped task: %r', vars(fact))
                        for listener in self._listeners:
                            listener.on_fact_stopped(fact)
                time.sleep(polling_intervall)
        except (KeyboardInterrupt, SystemExit):
            pass
