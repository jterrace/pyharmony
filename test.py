#!/usr/bin/env python2

import argparse
import logging
import sys

import sleekxmpp
from sleekxmpp.xmlstream import ET

from harmony import auth


class SendMsgBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, **kwargs):
        super(SendMsgBot, self).__init__(jid, password, **kwargs)

        self.add_event_handler('session_start', self.start)

    def start(self, event):
        iq = self.Iq()
        iq['type'] = 'get'
        oa = ET.Element('oa')
        oa.attrib['xmlns'] = 'connect.logitech.com'
        oa.attrib['mime'] = 'vnd.logitech.harmony/vnd.logitech.harmony.engine?holdAction'
        oa.text = 'action={"type"::"IRCommand","deviceId"::"11586428","command"::"VolumeDown"}:status=press'
        iq.set_payload(oa)
        result = iq.send(block=True)
        payload = result.get_payload()
        self.disconnect(send_close=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test script for pyharmony.')
    parser.add_argument('username', help=('Logitech username. Should be in the '
                                          'form of an email address.'))
    parser.add_argument('password', help='Logitech password.')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    token = auth.login(args.username, args.password)
    if not token:
        sys.exit('Could not get token from Logitech server.')

    plugin_config = {}
    # Enables PLAIN authentication which is off by default.
    plugin_config['feature_mechanisms'] = {'unencrypted_plain': True}

    xmpp = auth.SwapAuthToken(token, 'guest@x.com', 'guest',
                         plugin_config=plugin_config)
    xmpp.connect(address=('192.168.1.115', 5222))
    xmpp.process(block=True)

    xmpp = SendMsgBot('%s@x.com' % xmpp.uuid, xmpp.uuid,
                      plugin_config=plugin_config)
    xmpp.connect(address=('192.168.1.115', 5222))
    xmpp.process(block=True)
