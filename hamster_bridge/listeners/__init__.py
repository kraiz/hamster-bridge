from collections import namedtuple


ConfigValue = namedtuple('ConfigValue', ['key', 'setup_func'])


class HamsterListener(object):

    short_name = None
    config_values = []

    def configure(self, config):
        self.config = config
        if self.short_name is not None and len(self.config_values) > 0:
            if not self.config.has_section(self.short_name):
                self.config.add_section(self.short_name)
            for cv in self.config_values:
                if not self.config.has_option(self.short_name, cv.key):
                    self.config.set(self.short_name, cv.key, cv.setup_func())

    def prepare(self):
        pass

    def on_fact_started(self, fact):
        pass

    def on_fact_stopped(self, fact):
        pass
