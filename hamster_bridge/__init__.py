import argparse
import logging

from hamster_bridge.bridge import HamsterBridge


logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)+7s: %(message)s')
logger = logging.getLogger(__name__)


def import_listener(name):
    components = name.rsplit('.')
    mod = __import__(name.rsplit('.', 1)[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


LISTENERS = [
    # TODO: do some fancy plugin loading mechanism here to allow loading other's listeners, contributions welcome!
    'hamster_bridge.listeners.jira.JiraHamsterListener',
    'hamster_bridge.listeners.redmine.RedmineHamsterListener',
]


def main():
    listener_choices = dict(
        (lc.short_name, lc) for lc in [import_listener(l) for l in LISTENERS]
    )

    parser = argparse.ArgumentParser(description='Let your hamster log your work to your favorite bugtracker.')
    parser.add_argument('bugtracker', choices=sorted(listener_choices.keys()))
    args = parser.parse_args()

    logger.info('Starting hamster bridge')
    bridge = HamsterBridge()
    logger.info('Activating listener: %s', args.bugtracker)
    bridge.add_listener(listener_choices[args.bugtracker]())
    bridge.configure()
    bridge.run()    

if __name__ == "__main__":
    main()
