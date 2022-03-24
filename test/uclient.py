import os, sys
import asyncio
from p2psc.udp_p2p import UdpP2P
from p2psc.p2phandler import P2PHandler
from appPublic.jsonConfig import getConfig
from appPublic.app_logger import create_logger

class Client(UdpP2P):
	def on_handshaked(self):
		self.debug('on_handshake() called')
		self.send(b'this is a test text')
		self.info('this is a test text --- send to server')

	def on_recv(self, data, addr):
		d = data.decode('utf-8')
		self.info('data receive=%s', d)
		self.stop()
		loop = asyncio.get_event_loop()
		loop.stop()
		self.debug('loop=%s', loop)

if __name__ == '__main__':
	pwd = os.getcwd()
	config = getConfig(pwd)
	if len(sys.argv) < 2:
		print('Usage:\n%s peerid', sys.argv[1])
		sys.exit(1)

	logger = create_logger('uclient', levelname='debug')
	loop = asyncio.get_event_loop()
	p2p = P2PHandler(loop=loop)
	c = loop.run_until_complete( p2p.connect_udp_peer(sys.argv[1], ProtocolClass=Client))
	logger.debug('loop=%s', loop)
	loop.run_forever()
