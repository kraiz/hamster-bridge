import logging

from hamster_bridge.bridge import HamsterBrigde

logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)+7s: %(message)s')
logger = logging.getLogger(__name__)

LISTENERS = [
    # TODO: do some fancy plugin loading mechanism here to allow loading other's listeners, contributions welcome!
    'hamster_bridge.listeners.jira.JiraHamsterListener'
]


def import_listener(name):
    components = name.rsplit('.')
    mod = __import__(name.rsplit('.', 1)[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def main():
    logger.info('Starting hamster bridge')
    bridge = HamsterBrigde()
    for listener in LISTENERS:
        logger.info('Found listener: %s', listener)
        bridge.add_listener(import_listener(listener)())
    bridge.configure()
    bridge.run()


if __name__ == "__main__":
    main()