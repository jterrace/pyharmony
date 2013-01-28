import logging
import sleekxmpp


PASSWORD = '2bbc2f7c-b29a-4428-9439-5bd0757196ad'
USERNAME = '2bbc2f7c-b29a-4428-9439-5bd0757196ad'


class SendMsgBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, **kwargs):
        super(SendMsgBot, self).__init__(jid, password, **kwargs)

        self.add_event_handler('session_start', self.start)

    def start(self, event):
        self.send_presence()
        self.get_roster()

        self.send_message(mto=self.recipient, mbody=self.msg)

        self.disconnect(wait=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    plugin_config = {}
    plugin_config['feature_mechanisms'] = {'unencrypted_plain': True}

    xmpp = SendMsgBot('%s@x.com' % USERNAME, PASSWORD, plugin_config=plugin_config)
    xmpp.connect(address=('192.168.1.115', 5222))
    xmpp.process(block=True)
