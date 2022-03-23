import os, sys
import asyncio
from p2psc.p2p import TcpP2P
from p2psc.p2phandler import P2PHandler
from appPublic.jsonConfig import getConfig

class Client(TcpP2P):
	def on_handshaked(self):
		self.send(b'this is a test text')

	def on_recv(self, data):
		d = data.decode('utf-8')
		print('data receive=', d)
		self.transport.close()
		loop = asyncio.get_running_loop()
		loop.stop()

if __name__ == '__main__':
	pwd = os.getcwd()
	config = getConfig(pwd)
	if len(sys.argv) < 2:
		print('Usage:\n%s peerid', sys.argv[1])
		sys.exit(1)

	loop = asyncio.get_event_loop()
	p2p = P2PHandler(loop=loop)
	c = loop.run_until_complete( p2p.connect_peer(sys.argv[1], ProtocolClass=Client))
	loop.run_forever()
