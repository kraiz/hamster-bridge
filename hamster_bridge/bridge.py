import ConfigParser
import datetime
import time
import logging
import os

logger = logging.getLogger(__name__)

CONFIG_PATH = '~/.hamster-bridge.cfg'

try:
    import hamster.client
except ImportError:
    raise ImportError('Can not find hamster')


class HamsterBridge(hamster.client.Storage):
    """
    Connects to the running hamster instance via dbus. But as the notification does not work reliable there is a
    polling-based loop in the run()-method that will trigger all registered listeners.
    """
    def __init__(self):
        super(HamsterBridge, self).__init__()
        self._listeners = []

    def add_listener(self, listener):
        """
        Registers the given HamsterListener instance. It will then be notified about changes.

        :param listener: the HamsterListener instance
        :type  listener: HamsterListener
        """
        if listener not in self._listeners:
            logger.info('Registering %s' % listener)
            self._listeners.append(listener)

    def configure(self):
        """
        Gives each listener the chance to do something before we start the bridge's runtime loops.
        """
        path = os.path.expanduser(CONFIG_PATH)
        config = ConfigParser.RawConfigParser()
        # read from file if exists
        if os.path.exists(path):
            config.read(path)
        # let listeners extend
        for listener in self._listeners:
            listener.configure(config)
        # save to file
        with open(path, 'wb') as configfile:
            config.write(configfile)

    def run(self, polling_intervall=1):
        """
        Starts the polling loop that will run until receive common exit signals.

        :param polling_intervall: how often the connector polls data from haster in seconds (default: 1)
        :type  polling_intervall: int
        """
        try:
            for listener in self._listeners:
                listener.prepare()
            while True:
                now = datetime.datetime.now().replace(microsecond=0)
                last = now - datetime.timedelta(seconds=polling_intervall)
                for fact in self.get_todays_facts():
                    if fact.start_time is not None and last <= fact.start_time < now:
                        for listener in self._listeners:
                            listener.on_fact_started(fact)
                    if fact.end_time is not None and last <= fact.end_time < now:
                        for listener in self._listeners:
                            listener.on_fact_stopped(fact)
                time.sleep(polling_intervall)
        except (KeyboardInterrupt, SystemExit):
            pass
