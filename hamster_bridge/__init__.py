import argparse
import logging

from hamster_bridge.bridge import HamsterBridge


def import_listener(name):
    components = name.rsplit('.')
    mod = __import__(name.rsplit('.', 1)[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


LISTENERS = [
    'hamster_bridge.listeners.jira.JiraHamsterListener',
    'hamster_bridge.listeners.redmine.RedmineHamsterListener',
    # your backend missing? contributions welcome!
]


def main():
    listener_choices = dict(
        (lc.short_name, lc) for lc in [import_listener(l) for l in LISTENERS]
    )

    parser = argparse.ArgumentParser(description='Let your hamster log your work to your favorite bugtracker.')
    parser.add_argument('bugtracker', choices=sorted(listener_choices.keys()))
    parser.add_argument('-d', '--debug', action='store_true', help='enable debug logging')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)-15s %(levelname)+7s{}: %(message)s'.format(' [%(name)s]' if args.debug else '')
    )
    logger = logging.getLogger(__name__)

    logger.info('Starting hamster bridge')
    bridge = HamsterBridge()
    logger.debug('Activating listener: %s', args.bugtracker)
    bridge.add_listener(listener_choices[args.bugtracker]())
    bridge.configure()
    bridge.run()    

if __name__ == "__main__":
    main()
