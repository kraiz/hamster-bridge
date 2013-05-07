

class HamsterListener(object):

    short_name = None
    config_values = []

    def configure(self, config):
        self.config = config
        if self.short_name is not None and len(self.config_values) > 0:
            if not self.config.has_section(self.short_name):
                self.config.add_section(self.short_name)
            for config_key, config_value in self.config_values:
                if not self.config.has_option(self.short_name, config_key):
                    self.config.set(self.short_name, config_key, config_value())

    def prepare(self):
        pass

    def on_fact_started(self, fact):
        pass

    def on_fact_stopped(self, fact):
        pass