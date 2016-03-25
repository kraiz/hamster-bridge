import argparse
import logging

from hamster_bridge.bridge import HamsterBridge


CONFIG_PATH = '~/.hamster-bridge.cfg'


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
    parser.add_argument('-c', '--check-interval', default='2', type=int,
                        help='check every this amount of seconds for updates')
    parser.add_argument('--config-path', default=CONFIG_PATH, type=str, 
                        help='path to config file, defaults to {}'.format(CONFIG_PATH))
    parser.add_argument('--save-passwords', action='store_true',
                        help='store passwords and other sensitive data in the config file, defaults to False.')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)-15s %(levelname)+7s{}: %(message)s'.format(' [%(name)s]' if args.debug else '')
    )
    logger = logging.getLogger(__name__)

    logger.info('Starting hamster bridge')
    bridge = HamsterBridge(save_passwords=args.save_passwords)
    logger.debug('Activating listener: %s', args.bugtracker)
    bridge.add_listener(listener_choices[args.bugtracker]())
    bridge.configure(args.config_path)
    logger.debug('Run with check interval of %ds', args.check_interval)
    bridge.run(args.check_interval)

if __name__ == "__main__":
    main()
