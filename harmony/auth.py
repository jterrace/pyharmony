# Copyright (c) 2013, Jeff Terrace
# All rights reserved.

"""Contains authentication routines."""

import json
import logging
import re

import requests
import sleekxmpp
from sleekxmpp.xmlstream import ET

LOGGER = logging.getLogger(__name__)

# The Logitech authentication service URL.
LOGITECH_AUTH_URL = ('https://svcs.myharmony.com/CompositeSecurityServices/'
                     'Security.svc/json/GetUserAuthToken')


def login(username, password):
    """Logs in to the Logitech Harmony web service.

    Args:
      username: The username (email address).
      password: The user's password.

    Returns:
      A base64-encoded string containing a 48-byte Login Token.
    """
    headers = {'content-type': 'application/json; charset=utf-8'}
    data = {'email': username, 'password': password}
    data = json.dumps(data)
    r = requests.post(LOGITECH_AUTH_URL, headers=headers, data=data)
    if r.status_code != 200:
        LOGGER.error('Received response code %d from Logitech.', r.status_code)
        LOGGER.error('Data: \n%s\n', r.text)
        return

    result = r.json().get('GetUserAuthTokenResult', None)
    if not result:
        LOGGER.error('Malformed JSON (GetUserAuthTokenResult): %s', r.json)
        return
    token = result.get('UserAuthToken', None)
    if not token:
        LOGGER.error('Malformed JSON (UserAuthToken): %s', r.json)
        return
    return token


class SwapAuthToken(sleekxmpp.ClientXMPP):
    """An XMPP client for swapping a Login Token for a Session Token.

    After the client finishes processing, the uuid attribute of the class will
    contain the session token.
    """

    def __init__(self, token, *args, **kwargs):
        """Initializes the client.

        Args:
          token: The base64 string containing the 48-byte Login Token.
        """
        super(SwapAuthToken, self).__init__(*args, **kwargs)

        self.token = token
        self.uuid = None
        self.add_event_handler('session_start', self.start)

    def start(self, event):
        iq = self.Iq()
        iq['type'] = 'get'
        oa = ET.Element('oa')
        oa.attrib['xmlns'] = 'connect.logitech.com'
        oa.attrib['mime'] = 'vnd.logitech.connect/vnd.logitech.pair'
        oa.text = 'token=%s:name=%s' % (self.token, 'foo#iOS6.0.1#iPhone')
        iq.set_payload(oa)
        result = iq.send(block=True)
        payload = result.get_payload()
        assert len(payload) == 1
        oa = payload[0]
        assert oa.attrib['errorcode'] == '200'
        m = re.search(r'identity=(?P<uuid>[\w-]+):status', oa.text)
        assert m
        self.uuid = m.group('uuid')
        LOGGER.info('Received UUID from device: %s', self.uuid)
        self.disconnect(send_close=False)
