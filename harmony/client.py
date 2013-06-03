"""Client class for connecting to the Logitech Harmony."""

import json
import logging
import time

import sleekxmpp
from sleekxmpp.xmlstream import ET


LOGGER = logging.getLogger(__name__)


class HarmonyClient(sleekxmpp.ClientXMPP):
    """An XMPP client for connecting to the Logitech Harmony."""

    def __init__(self, auth_token):
        user = '%s@x.com' % auth_token
        password = auth_token
        plugin_config = {
            # Enables PLAIN authentication which is off by default.
            'feature_mechanisms': {'unencrypted_plain': True},
        }
        super(HarmonyClient, self).__init__(
            user, password, plugin_config=plugin_config)

    def get_config(self):
        """Retrieves the Harmony device configuration.

        Returns:
          A nested dictionary containing activities, devices, etc.
        """
        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'
        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = (
            'vnd.logitech.harmony/vnd.logitech.harmony.engine?config')
        iq_cmd.set_payload(action_cmd)
        result = iq_cmd.send(block=True)
        payload = result.get_payload()
        assert len(payload) == 1
        action_cmd = payload[0]
        assert action_cmd.attrib['errorcode'] == '200'
        device_list = action_cmd.text
        return json.loads(device_list)


def create_and_connect_client(ip_address, port, token):
    """Creates a Harmony client and initializes session.

    Args:
      ip_address: IP Address of the Harmony device.
      port: Port that the Harmony device is listening on.
      token: A string containing a session token.

    Returns:
      An instance of HarmonyClient that is connected.
    """
    client = HarmonyClient(token)
    client.connect(address=(ip_address, port),
                   use_tls=False, use_ssl=False)
    client.process(block=False)

    while not client.sessionstarted:
        time.sleep(0.1)

    return client
