import os, sys
import asyncio
from p2psc.p2phandler import P2PHandler
from p2psc.udp_p2p import UdpP2P
from appPublic.jsonConfig import getConfig
from appPublic.app_logger import create_logger

class Server(UdpP2P):
	def on_recv(self, data, addr):
		self.debug('data=%s, addr=%s', data, addr)
		self.send(b'recv:' + data, addr)

if __name__ == '__main__':
	pwd = os.getcwd()
	config = getConfig(pwd)
	logger = create_logger('userver', levelname='debug')
	loop = asyncio.get_event_loop()
	p2p = P2PHandler(loop=loop)
	loop.run_until_complete(p2p.run_as_udp_server(ProtocolClass=Server))
	loop.run_forever()
