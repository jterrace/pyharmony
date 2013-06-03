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
    resp = requests.post(LOGITECH_AUTH_URL, headers=headers, data=data)
    if resp.status_code != 200:
        LOGGER.error('Received response code %d from Logitech.',
                     resp.status_code)
        LOGGER.error('Data: \n%s\n', resp.text)
        return

    result = resp.json().get('GetUserAuthTokenResult', None)
    if not result:
        LOGGER.error('Malformed JSON (GetUserAuthTokenResult): %s', resp.json())
        return
    token = result.get('UserAuthToken', None)
    if not token:
        LOGGER.error('Malformed JSON (UserAuthToken): %s', resp.json())
        return
    return token


class SwapAuthToken(sleekxmpp.ClientXMPP):
    """An XMPP client for swapping a Login Token for a Session Token.

    After the client finishes processing, the uuid attribute of the class will
    contain the session token.
    """

    def __init__(self, token):
        """Initializes the client.

        Args:
          token: The base64 string containing the 48-byte Login Token.
        """
        plugin_config = {
            # Enables PLAIN authentication which is off by default.
            'feature_mechanisms': {'unencrypted_plain': True},
        }
        super(SwapAuthToken, self).__init__(
            'guest@x.com', 'guest', plugin_config=plugin_config)

        self.token = token
        self.uuid = None
        self.add_event_handler('session_start', self.session_start)

    def session_start(self, _):
        """Called when the XMPP session has been initialized."""
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = 'vnd.logitech.connect/vnd.logitech.pair'
        action_cmd.text = 'token=%s:name=%s' % (self.token,
                                                'foo#iOS6.0.1#iPhone')
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=True)
        payload = result.get_payload()
        assert len(payload) == 1
        oa_resp = payload[0]
        assert oa_resp.attrib['errorcode'] == '200'
        match = re.search(r'identity=(?P<uuid>[\w-]+):status', oa_resp.text)
        assert match
        self.uuid = match.group('uuid')
        LOGGER.info('Received UUID from device: %s', self.uuid)
        self.disconnect(send_close=False)


def swap_auth_token(ip_address, port, token):
    """Swaps the Logitech auth token for a session token.

    Args:
      ip_address: IP Address of the Harmony device.
      port: Port that the Harmony device is listening on.
      token: A base64-encoded string containing a 48-byte Login Token.

    Returns:
      A string containing the session token.
    """
    login_client = SwapAuthToken(token)
    login_client.connect(address=(ip_address, port),
                         use_tls=False, use_ssl=False)
    login_client.process(block=True)
    return login_client.uuid
