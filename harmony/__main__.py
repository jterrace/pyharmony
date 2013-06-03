#!/usr/bin/env python2

"""Command line utility for querying the Logitech Harmony."""

import argparse
import logging
import pprint
import sys

from harmony import auth
from harmony import client as harmony_client


def login_to_logitech(args):
    """Logs in to the Logitech service.

    Args:
      args: argparse arguments needed to login.

    Returns:
      Session token that can be used to log in to the Harmony device.
    """
    token = auth.login(args.email, args.password)
    if not token:
        sys.exit('Could not get token from Logitech server.')

    session_token = auth.swap_auth_token(
        args.harmony_ip, args.harmony_port, token)
    if not session_token:
        sys.exit('Could not swap login token for session token.')

    return session_token


def show_config(args):
    """Connects to the Harmony and prints its configuration."""
    token = login_to_logitech(args)
    client = harmony_client.create_and_connect_client(
        args.harmony_ip, args.harmony_port, token)
    pprint.pprint(client.get_config())
    client.disconnect(send_close=False)
    return 0


def main():
    """Main method for the script."""
    parser = argparse.ArgumentParser(
        description='pyharmony utility script',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Required flags go here.
    required_flags = parser.add_argument_group('required arguments')
    required_flags.add_argument('--email', required=True, help=(
        'Logitech username in the form of an email address.'))
    required_flags.add_argument(
        '--password', required=True, help='Logitech password.')
    required_flags.add_argument(
        '--harmony_ip', required=True, help='IP Address of the Harmony device.')

    # Flags with defaults go here.
    parser.add_argument('--harmony_port', default=5222, type=int, help=(
        'Network port that the Harmony is listening on.'))
    loglevels = dict((logging.getLevelName(level), level)
                     for level in [10, 20, 30, 40, 50])
    parser.add_argument('--loglevel', default='INFO', choices=loglevels.keys(),
        help='Logging level to print to the console.')

    subparsers = parser.add_subparsers()
    list_devices_parser = subparsers.add_parser(
        'show_config', help='Print the Harmony device configuration.')
    list_devices_parser.set_defaults(func=show_config)

    args = parser.parse_args()

    logging.basicConfig(
        level=loglevels[args.loglevel],
        format='%(levelname)s\t%(name)s\t%(message)s')

    sys.exit(args.func(args))


if __name__ == '__main__':
    main()
