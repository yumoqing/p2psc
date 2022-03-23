import os, sys
import asyncio
from p2psc.p2phandler import P2PHandler
from p2psc.p2p import TcpP2P
from appPublic.jsonConfig import getConfig

class Server(TcpP2P):
	def on_recv(self, data):
		self.send(b'recv:' + data)

if __name__ == '__main__':
	pwd = os.getcwd()
	config = getConfig(pwd)
	loop = asyncio.get_event_loop()
	p2p = P2PHandler(loop=loop)
	loop.run_until_complete(p2p.run_as_server(ProtocolClass=Server))
	loop.run_forever()
