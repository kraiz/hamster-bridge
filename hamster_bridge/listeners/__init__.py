from collections import namedtuple
from ConfigParser import NoOptionError


ConfigValue = namedtuple('ConfigValue', ['key', 'setup_func', 'sensitive'])


class HamsterListener(object):

    short_name = None
    config_values = []

    def get_from_config(self, key):
        """
        Tries to get the value for the specified key. First in the regular
        config, then in the sensitive_config. If it not found in either None is
        returned.
        """
        try:
            # Get from regular config
            value = self.config.get(self.short_name, key)
        except NoOptionError:
            try:
                # ... if not found get from sensitive config
                value = self.sensitive_config.get(self.short_name, key)
            except NoOptionError:
                # ... if again not found return None
                value = None
        return value


    def configure(self, config, sensitive_config):
        """
        Saves selve.config_values in 'config' or 'sensitive_config' depending
        on whether the config value is sensitive information (e.g. a password)
        or not.
        """
        self.config = config
        self.sensitive_config = sensitive_config
        if self.short_name is not None and len(self.config_values) > 0:
            if not self.config.has_section(self.short_name):
                self.config.add_section(self.short_name)
            if not self.sensitive_config.has_section(self.short_name):
                self.sensitive_config.add_section(self.short_name)
            for cv in self.config_values:
                if cv.sensitive:
                    if self.get_from_config(cv.key) is None:
                        self.sensitive_config.set(
                            self.short_name,
                            cv.key,
                            cv.setup_func(),
                        )
                else:
                    if self.get_from_config(cv.key) is None:
                        self.config.set(
                            self.short_name,
                            cv.key,
                            cv.setup_func(),
                        )

    def prepare(self):
        pass

    def on_fact_started(self, fact):
        pass

    def on_fact_stopped(self, fact):
        pass
