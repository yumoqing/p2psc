import os, sys
import asyncio
from p2psc.udp_p2psc import SecUdp
from p2psc.pubkey_handler import PubkeyHandler
from appPublic.jsonConfig import getConfig
from appPublic.app_logger import create_logger

class Client(SecUdp):
	def on_handshaked(self):
		self.send_cnt = 0
		self.send_timly()

	def send_timly(self, *args):
		loop = self.handler.loop
		task = loop.call_later(10, self.send_timly)
		self.send(b'test text repeatly 10 seconds', self.remote_addr) 
		self.send_cnt += 1
		if self.send_cnt > 10:
			task.cancel()
			self.stop()
			loop.stop()

	def on_recv(self, data, addr):
		d = data.decode('utf-8')
		self.info('data receive=%s', d)

if __name__ == '__main__':
	pwd = os.getcwd()
	config = getConfig(pwd)
	if len(sys.argv) < 2:
		print('Usage:\n%s peerid', sys.argv[1])
		sys.exit(1)

	logger = create_logger('uclient', levelname='debug')
	loop = asyncio.get_event_loop()
	handler = PubkeyHandler()
	c = loop.run_until_complete( handler.connect_udp_peer(sys.argv[1], ProtocolClass=Client))
	loop.run_forever()
