import os, sys
import asyncio
from p2psc.pubkey_handler import PubkeyHandler
from p2psc.udp_p2psc import SecUdp
from appPublic.jsonConfig import getConfig
from appPublic.app_logger import create_logger

class Server(SecUdp):
	def on_recv(self, data, addr):
		self.debug('data=%s, addr=%s', data, addr)
		self.send(b'recv:' + data, addr)

	def set_idle_timeout(self):
		self.idle_timeout = 3
		self.info('new one')

if __name__ == '__main__':
	pwd = os.getcwd()
	config = getConfig(pwd)
	logger = create_logger('userver', levelname='debug')
	loop = asyncio.get_event_loop()
	handler = PubkeyHandler()
	loop.run_until_complete(handler.run_as_udp_server(ProtocolClass=Server))
	loop.run_forever()
